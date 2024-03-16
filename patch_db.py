import time

import requests

import database
from fake_useragent import UserAgent

# Initialize the UserAgent object
ua = UserAgent()


def fetch_repo_statics(repo_title: str) -> ():
    """
    获取仓库的watch folk and star数据
    :param repo_title:
    :return:
    """
    title_split = repo_title.split('/')
    username = title_split[0].strip()
    repo_name = title_split[1].strip()
    api_url = f'https://api.github.com/repos/{username}/{repo_name}'

    headers = {
        'User-Agent': ua.random,
        'Accept': 'application/vnd.github.v3+json',
    }
    # print(f"current token: {GITHUB_TOKEN}")
    try:
        response = requests.get(api_url, headers=headers)
        # response.raise_for_status()  # Check for errors
        if response.status_code == 404:
            print(f">>> 当前仓库404状态，已被删除: {username}/{repo_name}")
            return 0, 0, 0, False
        if response.status_code != 200:
            print(f">>> 当前请求可能触发Github api limit限制.")
            print(f">>> {response.text}")
            return 0, 0, 0, False
        repo_data = response.json()

        watch_count = repo_data.get('subscribers_count', 0)
        forks_count = repo_data.get('forks_count', 0)
        stars_count = repo_data.get('stargazers_count', 0)

        # watch,folk,star,is_exist
        return watch_count, forks_count, stars_count, True

    except requests.exceptions.RequestException as e:
        print(f">>> Error fetching data: {e}")

    return None


def patch_db_with_repo_info():
    # repo_star=0 and repo_status =1
    need_to_patch = database.session.query(
        database.GithubTrending).filter_by(repo_star=0, repo_status=1).all()
    for repo in need_to_patch:
        # fetch repo data
        statics = fetch_repo_statics(repo.title)
        if statics is not None and statics[3] is True:
            repo.repo_see = statics[0]
            repo.repo_folk = statics[1]
            repo.repo_star = statics[2]
            repo.repo_status = 1
            print(f">>>: {statics}")
            try:
                database.session.commit()
            except Exception as e:
                print("Failed to patch repo data: " + str(e))
                database.session.rollback()
                continue
            print(f"Patching repo data success: {repo.title}")
        else:
            print(f"Failed to get repo data: {repo.title}")
            print(f"May be the repo does not exist: {repo.url}")
        time.sleep(3)


if __name__ == '__main__':
    patch_db_with_repo_info()
