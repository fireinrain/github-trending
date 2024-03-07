import time

from database import session
from database import GithubTrending
from scraper import fetch_repo_statics


def patch_db_with_repo_info():
    need_to_patch = session.query(GithubTrending).filter_by(repo_star=0).filter_by(repo_status=1).all()
    for repo in need_to_patch:
        # fetch repo data
        statics = fetch_repo_statics(repo.title)
        if statics is not None and statics[3] is True:
            repo.repo_see = statics[0]
            repo.repo_folk = statics[1]
            repo.repo_star = statics[2]
            repo.repo_status = 0
            try:
                session.commit()
            except Exception as e:
                print("Failed to patch repo data: " + str(e))
                session.rollback()
                continue
            print(f"Patching repo data success: {repo.title}")
        else:
            print(f"Failed to get repo data: {repo.title}")
            print(f"May be the repo does not exist: {repo.url}")
        time.sleep(10)


if __name__ == '__main__':
    patch_db_with_repo_info()
