import json

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from .job_post import JobPost


def main(
    search: str | None = None,
    numb_pages: int = 1,
    destination_folder: str | None = None,
    drop_invalid: bool = True,
) -> dict[str, JobPost]:
    """Return a collection of scraped information from the website indeed.uk
    given some search terms.

    The search results are both saved into a json file and returned as a
    dictionary in the form job_id : JobPost object.

    Parameters
    ----------
    search : str | None, optional
        The search term(s) to be used. For example 'Data Scientist'. If None,
        an input window will ask for the search term during the function
        execution. By default None.
    numb_pages : int, optional
        Number of result pages to be scraped. Each page contains roughly 15
        results, by default 1. Note that an excessively high number might
        result in the script getting blocked by the website.
    destination_folder : str, optional
        Folder in the current working directory where the output json file
        should be placed. If None, the file is placed directly in the current
        working directory. By default None.
    drop_invalid : bool, optional
        If True, only the job posts with a title are kept. Jobs posts might not
        have a title - and any other info - if the script is blocked by the
        website. By default True.

    Returns
    -------
    dict[str, JobPost]
        Dictionary in the form 'job id' : 'job post info', where 'job id' is a
        string and 'job post info' is a JobPost object.
    """
    if search is None:
        search = input("Please provide the search terms:\n")

    single_url = search_to_url(search)
    pages_urls = url_to_pages(single_url, numb_pages)

    job_ids = set()
    print("Looking for job ids across the results pages...")
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

    if drop_invalid:
        drop_invalid_jobs(jobs_dict)

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
        f"Research completed: retrived {valid_jobs} valid results",
        f"out of {len(jobs_dict)} total jobs identified." "",
    )


def drop_invalid_jobs(jobs_dict: dict[str, JobPost]) -> None:
    for job_id, job in jobs_dict.items():
        if job.title is None:
            del jobs_dict[job_id]
