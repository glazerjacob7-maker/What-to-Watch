from collections import defaultdict
import json
from math import sqrt
import random

class MovieRecommender:
    def __init__(self, movie_info_filename: str, user_ratings_filename: str):
        """
        Inputs:
        movie_info_filename: name of JSON file containing
        mapping of movie IDs to info
        user_ratings_filename: name of JSON file containing
         mapping of user IDs to ratings
        """
        movie_info_file = open(movie_info_filename, "r")
        user_ratings_file = open(user_ratings_filename, "r")

        self.movie_info = MovieRecommender.read_from_json(movie_info_file)
        self.all_user_ratings = MovieRecommender.read_from_json(
            user_ratings_file
        )

        movie_info_file.close()
        user_ratings_file.close()

        # build every user’s genre -> average-score profile
        self.all_user_preferences = {
            int(user_id): self.ratings_to_preferences(user_ratings)
            for user_id, user_ratings in self.all_user_ratings.items()
        }

    @staticmethod
    def read_from_json(file):
        """
        You don't need to do anything with this function!
        Inputs:
        file:   pointer to file containing the dictionary to process

        Returns:
        The dictionary represented by the JSON, transforming all string
        keys into int keys for consistency.
        """
        dictionary = {int(k): v for k, v in json.load(file).items()}
        for key in dictionary:
            value = dictionary[key]
            if isinstance(value, dict):
                dictionary[key] = {int(k): v for k, v in value.items()}
        return dictionary

    def add_new_ratings(self, new_ratings_filename: str):
        """
        You don't need to do anything with this function!
        Inputs:
        new_ratings_filename:   file of new ratings JSON to include.
        """
        new_ratings_file = open(new_ratings_filename, "r")
        new_ratings = MovieRecommender.read_from_json(new_ratings_file)
        new_ratings_file.close()

        new_preferences = {
            int(user_id): self.ratings_to_preferences(user_ratings)
            for user_id, user_ratings in new_ratings.items()
        }
        self.all_user_ratings.update(new_ratings)
        self.all_user_preferences.update(new_preferences)

    def ratings_to_preferences(
        self, user_ratings: dict[int, float]
    ) -> dict[str, float]:
        """
        Inputs:
        user_ratings   -   mapping of movie IDs to ratings representing one user's ratings.

        Returns:
        dict mapping movie genres to the average rating that the user awards
        to movies from that genre. If the user has never seen a movie
        belonging to some particular genre, then that genre will not be
        present as a key in dictionary that is returned
        """

        totals = {}
        counts = {}

        for movie_id, score in user_ratings.items():
            if movie_id in self.movie_info:
                _title, genres = self.movie_info[movie_id]
                for genre in genres:
                    totals[genre] = totals.get(genre, 0.0) + score
                    counts[genre] = counts.get(genre, 0) + 1

        # Compute averages
        averages = {}
        for genre, total in totals.items():
            averages[genre] = total / counts[genre]
        return averages

    @staticmethod
    def cosine_similarity(
        first: dict[str, float], second: dict[str, float]
    ) -> float:
        """Calculates the cosine similarity between the two users' ratings profiles.

        Args:
            first (dict[str, float]): first user's ratings profile
            second (dict[str, float]): second user's ratings profile

        Returns:
            float: cosine similarity of the two users' ratings profiles.
        """

        # Genres common to both users
        shared = set(first) & set(second)
        if not shared:
            return 0.0

        # Dot product over shared genres
        dot_product = sum(first[g] * second[g] for g in shared)

        # Vector magnitudes
        mag_first = sqrt(sum(v * v for v in first.values()))
        mag_second = sqrt(sum(v * v for v in second.values()))

        if mag_first == 0 or mag_second == 0:
            return 0.0

        return dot_product / (mag_first * mag_second)

    def find_similar_user_by_id(self, user_id: int) -> int:
        """Find the ID of a user who has the preferences
        that are most similar to the user whose ID was
        passed in as input.

        Args:
            user_id (int): ID of the user to find another similar user to

        Returns:
            int: id of the user with preferences most similar to the input
                 user; ties broken in favor of higher ID values.
        """
        target_prefs = self.all_user_preferences[user_id]

        best_similarity = -1.0
        best_match_id = -1

        for other_id, other_prefs in self.all_user_preferences.items():
            if other_id != user_id:
                similarity = self.cosine_similarity(target_prefs, other_prefs)

                # choose a higher similarity, or higher ID on an exact tie
                better_similarity = similarity > best_similarity
                same_similarity = similarity == best_similarity and other_id > best_match_id

                if better_similarity or same_similarity:
                    best_similarity = similarity
                    best_match_id = other_id

        return best_match_id

    def make_recommendations_for_id(
        self, recommender_id: int, recipient_id: int
    ) -> set[str]:
        """Given a user who wants recommendations and another user, return a set of up to five
        movie names as recommendations.

        Args:
            recommender_id (int): id of the user whose ratings will be used as recommendation
            recipient_id (int): id of the user who wants a recommendation

        Returns:
            set[str]: a set of up to five movie titles. These movies must meet the criteria that
                      the recipient has not rated them, they are tagged with at least one of
                      the recipient's top two rated genres, and they are the most highly rated
                      movies by the recommender that meet the previous two conditions.
        """
        result = set()

        if recipient_id not in self.all_user_preferences:
            return result

        recipient_prefs = self.all_user_preferences[recipient_id]
        if len(recipient_prefs) == 0:
            return result

        pairs = list(recipient_prefs.items())
        pairs.sort(key=lambda pair: (-pair[1], pair[0]))

        top_genres_list = []
        index = 0
        while index < len(pairs) and len(top_genres_list) < 2:
            top_genres_list.append(pairs[index][0])
            index += 1

        recommender_ratings = self.all_user_ratings[recommender_id]
        recipient_seen = self.all_user_ratings[recipient_id]

        candidates = []

        for movie_id, rating in recommender_ratings.items():
            not_seen = movie_id not in recipient_seen
            in_metadata = movie_id in self.movie_info
            if not_seen and in_metadata:
                title, genres = self.movie_info[movie_id]

                genre_overlap = len(set(top_genres_list) & set(genres)) > 0
                if genre_overlap:
                    candidates.append((title, rating))

        candidates.sort(key=lambda t: (-t[1], t[0]))

        index = 0
        while index < len(candidates) and index < 5:
            result.add(candidates[index][0])
            index += 1

        return result
