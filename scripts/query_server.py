import time

import requests

BASE_URL = "http://localhost:5001"

def create_remote(name, url, policy="immediate"):
    remote_data = {
        "name": name,
        "url": url,
        "policy": policy,
    }
    response = requests.post(f"{BASE_URL}/pulp/api/v3/remotes/r/", json=remote_data)
    response.raise_for_status()
    return response.json()["pulp_href"]

def create_repository(name, remote_href):
    repository_data = {
        "name": name,
        "remote": remote_href,
    }
    response = requests.post(f"{BASE_URL}/pulp/api/v3/repositories/r/", json=repository_data)
    response.raise_for_status()
    return response.json()["pulp_href"]

def sync_repository(repository_href, remote_href):
    sync_data = {
        "remote": remote_href,
    }
    response = requests.post(f"{BASE_URL}{repository_href}sync/", json=sync_data)
    response.raise_for_status()
    task_href = response.json()["task"]
    wait_for_task(task_href)

def publish_repository(repository_href):
    publication_data = {
        "repository_version": f"{repository_href}versions/1/",
    }
    response = requests.post(f"{BASE_URL}/pulp/api/v3/publications/r/", json=publication_data)
    response.raise_for_status()
    task_href = response.json()["task"]
    wait_for_task(task_href)
    return response.json()["pulp_href"]

def create_distribution(name, base_path, publication_href):
    distribution_data = {
        "name": name,
        "base_path": base_path,
        "publication": publication_href,
    }
    response = requests.post(f"{BASE_URL}/pulp/api/v3/distributions/r/", json=distribution_data)
    response.raise_for_status()
    return response.json()["pulp_href"]

def wait_for_task(task_href, interval=1):
    while True:
        response = requests.get(f"{BASE_URL}{task_href}")
        response.raise_for_status()
        task_state = response.json()["state"]
        if task_state in ["completed", "failed", "canceled"]:
            break
        time.sleep(interval)

def main():
    remote_name = "r-remote"
    remote_url = "https://r.r-project.org"
    repository_name = "r-repo"
    distribution_name = "r-dist"
    distribution_base_path = "r"

    remote_href = create_remote(remote_name, remote_url)
    print(f"Created remote: {remote_href}")

    repository_href = create_repository(repository_name, remote_href)
    print(f"Created repository: {repository_href}")

    sync_repository(repository_href, remote_href)
    print("Repository synced successfully")

    publication_href = publish_repository(repository_href)
    print(f"Published repository: {publication_href}")

    distribution_href = create_distribution(distribution_name, distribution_base_path, publication_href)
    print(f"Created distribution: {distribution_href}")

    print(f"R packages are now available at: {BASE_URL}{distribution_href}packages/")

if __name__ == "__main__":
    main()