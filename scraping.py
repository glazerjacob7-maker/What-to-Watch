import requests as re
from bs4 import BeautifulSoup


def scrape_movie_info(slug: str) -> dict[int, tuple[str, tuple[str]]]:
    """
    Returns { movie_id : (title, (genres, …)) } for every page in the dataset.
    """
    movie_data = {}
    page_number = "page_1.html"

    while page_number != "":
        response = re.get(slug + page_number)
        soup = BeautifulSoup(response.text, "html.parser")

        table = soup.find("table")
        rows = table.find_all("tr")[1:]

        for row in rows:
            cells = row.find_all("td")

            # movie ID → int for correct dict keys
            movie_id = int(cells[0].get_text().strip())

            # remove trailing " (YEAR)" safely
            raw_title = cells[1].get_text()
            title = raw_title.rsplit(" (", 1)[0].strip()

            genres = []
            genre_string = cells[3].get_text().strip()

            genres = [genre.strip() for genre in genre_string.split(",")]

            genres = tuple(genres)

            movie_data[movie_id] = (title, genres)

        nav_links = soup.find_all("a")
        page_number = nav_links[1]["href"]

    return movie_data

def scrape_ratings(
    slug: str, movie_ids: set[int]
) -> dict[int, dict[int, float]]:
    """
    Scrapes every ratings.html page for the given movie IDs and returns
    { user_id : { movie_id : rating } }.
    """
    user_data = {}

    for movie_id in movie_ids:
        # Build URL from parts
        base = slug
        middle = "ratings_"
        end = ".html"
        url = base + middle + str(movie_id) + end

        response = re.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        table = soup.find("table")
        rows = table.find_all("tr")[1:]  # skip header

        for row in rows:
            cells = row.find_all("td")

            user_id = int(cells[0].get_text().strip())
            rating = float(cells[1].get_text().strip())

            # Ensure inner dict exists, then store the rating
            if user_id not in user_data:
                user_data[user_id] = {}
            user_data[user_id][movie_id] = rating

    return user_data
