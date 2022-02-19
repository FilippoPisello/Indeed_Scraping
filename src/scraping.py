import json

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from .job_post import JobPost


def main(search: str | None = None, numb_pages: int = 1):
    if search is None:
        search = input("Please provide the search terms:\n")

    single_url = search_to_url(search)
    pages_urls = url_to_pages(single_url, numb_pages)

    i = 0
    job_ids = set()
    print("Looking for job ids...")
    for url in tqdm(pages_urls):
        soup = url_to_content(url)
        job_ids = job_ids.union(set(get_job_ids_from_soup(soup)))
    else:
        print(f"{len(job_ids)} job ids retrived correctly!\n")

    jobs_dict = {}
    print("Downloading job posts information...")
    for index, job_id in enumerate(tqdm(job_ids)):
        job_url = job_id_to_url(job_id)
        job_page = requests.get(job_url)
        job_soup = BeautifulSoup(job_page.content, "html.parser")
        jobs_dict[job_id] = JobPost.from_job_soup(job_soup=job_soup, job_id=job_id)

        if (index % 20 == 0) or ((index + 1) == len(jobs_dict)):
            save_jobs_to_json(jobs_dict, search, destination_folder)
    else:
        print_search_feedback(jobs_dict)

    return jobs_dict


def search_to_url(search: str) -> str:
    """Transform user search terms into ready to use URL"""
    search = search.lower().replace(" ", "%20")
    return f"https://uk.indeed.com/jobs?q={search}&l=United%20Kingdom"


def url_to_pages(url: str, number_pages: int) -> list[str]:
    return [url + f"&start={n * 10}" for n in range(0, number_pages)]


def url_to_content(url: str) -> requests.Response:
    page = requests.get(url)
    return BeautifulSoup(page.content, "html.parser")


def get_job_ids_from_soup(soup) -> list[str]:
    mosaic_zone = soup.find("div", {"id": "mosaic-zone-jobcards"})
    mosaic_zone = mosaic_zone.find("div", {"id": "mosaic-provider-jobcards"})
    a_results = mosaic_zone.find_all("a", href=True)
    return [a.get("data-jk") for a in a_results if a.get("data-jk") is not None]


def job_id_to_url(job_id: str) -> str:
    return f"https://uk.indeed.com/viewjob?jk={job_id}"


def save_jobs_to_json(
    jobs_dict: dict[str, JobPost], search: str, destination_folder: str | None
) -> None:
    json_data = {key: jobs_dict[key].__dict__ for key in jobs_dict}

    output_file_name = f"saved_jobs_{search}_.json"
    if destination_folder is not None:
        output_file_name = destination_folder + output_file_name

    with open(output_file_name, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)


def print_search_feedback(jobs_dict: dict[str, JobPost]) -> None:
    valid_jobs = len([j.title for _, j in jobs_dict.items() if j.title is not None])
    print(
        f"""Research completed: retrived {valid_jobs} valid results
          out of {len(jobs_dict)} total jobs identified."""
    )


