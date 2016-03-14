from pymongo import MongoClient, UpdateOne, InsertOne
from pymongo.errors import BulkWriteError
from datetime import datetime, timedelta
from config import DB_NAME, MARKETS_COLLECTION, MARKET_BOOK_COLLECTION, STATUS
from threading import Thread

# Connect to mongo database
c = MongoClient()
markets_col = c[DB_NAME][MARKETS_COLLECTION]
book_col = c[DB_NAME][MARKET_BOOK_COLLECTION]


class db_writer(Thread):
    def __init__(self, q):
        """

        :param db: mongodb to be written to
        :param q: Queue to write data from
        :return:
        """
        Thread.__init__(self)
        self.q = q

    def run(self):
        # receive item from queue
        data = self.q.get()

        # Process data to get it into format to save to mongodb

        # Check if market is no longer active
        if data.status == "CLOSED":
            # Write to events collection event status is now closed
            pass
        # Save to mongodb


        # Let queue know that task is complete
        self.q.task_done()


def clean_out_db():
    """
    Drops all tables and cleans the shit out of our database
    :return: None
    """
    c.drop_database(DB_NAME)


def write_markets_to_database(markets):
    """

    :param markets: Formated Markets from betfair (see models.txt for formating)
    :return: Instance of Mongodb InsertManyResult.
    """
    # write all changes into db
    return markets_col.insert_many(markets)


def write_books_to_database(books):
    """
    Writes books to database
    :param books: Books returned from betfair
    :return: Instance of mongodb InsertManyResult
    """
    market_updates = []  # Any markets that need to be closed

    # iterate through books and check if any markets are closed
    for book in books:
        if book["status"] == STATUS["CLOSED"]:
            market_updates.append(
                UpdateOne(
                    {"marketId": book["marketId"]},
                    {"$set": {"status": STATUS["CLOSED"]}}
                )
            )

    # TODO error correction if bulk writes don't work?
    try:
        if len(market_updates) > 0:
            markets_col.bulk_write(market_updates)
    except BulkWriteError as e:
        print(e.details)
    return book_col.insert_many(books)

def get_live_games_market_ids():
    """
    Reads games in events. Only returns markets who's games have started (i.e. inplay)
    and markets are not closed
    :return: List of market Ids (floats)
    """

    # Find games where openDates are
    # earlier than current time, but status is also open
    cur = markets_col.find(
        {"openDate":
             {"$lt": datetime.now()},
         "status":
             {"$gt": STATUS["CLOSED"]}
         })

    return [market["marketId"] for market in cur]
