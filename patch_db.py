# coding:utf-8
"""补录缺失的仓库统计数据(star/fork/watch), 供手动运行: python patch_db.py"""
import time

import database
from main import fetch_repo_stats


def patch_repo_stats():
    need_to_patch = database.session.query(
        database.GithubTrending).filter_by(repo_star=0, repo_status=1).all()
    for repo in need_to_patch:
        statics = fetch_repo_stats(repo.title)
        if statics is not None and statics[3] is True:
            repo.repo_see = statics[0]
            repo.repo_folk = statics[1]
            repo.repo_star = statics[2]
            repo.repo_status = 1
            print(f">>> 获取仓库信息成功: {statics}")
            try:
                database.session.commit()
            except Exception as e:
                print(f"Failed to patch repo data: {e}")
                database.session.rollback()
                continue
            print(f"Patching repo data success: {repo.title}")
        else:
            print(f"Failed to get repo data: {repo.title}")
            print(f"May be the repo does not exist: {repo.url}")
        time.sleep(3)


if __name__ == '__main__':
    patch_repo_stats()