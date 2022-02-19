from dataclasses import dataclass

from bs4 import BeautifulSoup, element


@dataclass
class JobPost:
    job_id: str
    title: str
    company: str
    salary: str
    rating_value: float
    rating_count: int
    contract_type: list[str]
    description: str

    @classmethod
    def from_job_soup(cls, job_soup: BeautifulSoup, job_id: str):
        title = cls.text_if_not_none(
            job_soup.find("h1", {"class": "jobsearch-JobInfoHeader-title"})
        )
        company = cls.text_if_not_none(
            job_soup.find("div", {"class": "jobsearch-CompanyReview--heading"})
        )
        salary = cls.text_if_not_none(
            job_soup.find("span", {"class": "attribute_snippet"})
        )
        rating_value = cls.text_if_not_none(
            job_soup.find("meta", {"itemprop": "ratingValue"}),
            as_content=True,
            new_type=float,
        )

        rating_count = cls.text_if_not_none(
            job_soup.find("meta", {"itemprop": "ratingCount"}),
            as_content=True,
            new_type=int,
        )

        contract_type = cls.text_if_not_none(
            job_soup.find("span", {"class": "jobsearch-JobMetadataHeader-item"})
        )
        if contract_type is not None:
            contract_type = contract_type.replace(" -  ", "").split(", ")
            contract_type = [c for c in contract_type if len(c) > 3]

        description = cls.text_if_not_none(
            job_soup.find("div", {"id": "jobDescriptionText"})
        )
        return cls(
            job_id=job_id,
            title=title,
            company=company,
            salary=salary,
            rating_value=rating_value,
            rating_count=rating_count,
            contract_type=contract_type,
            description=description,
        )

    @staticmethod
    def text_if_not_none(
        soup_search: element.Tag | None, as_content: bool = False, new_type=None
    ):
        if soup_search is not None:

            if as_content:
                output = soup_search["content"]
            else:
                output = soup_search.text

            if new_type is not None:
                return new_type(output)
            return output

        return None
