# ----- CONFIGURE YOUR EDITOR TO USE 4 SPACES PER TAB ----- #
import settings
import sys,os
import random
sys.path.append(os.path.join(os.path.split(os.path.abspath(__file__))[0], 'lib'))
import pymysql as db

def connection():
    ''' User this function to create your connections '''
    con = db.connect(
        settings.mysql_host,
        settings.mysql_user,
        settings.mysql_passwd,
        settings.mysql_schema)
    return con

def classify_review(reviewid):
    # Create a new connection
    con=connection()
    # Create a cursor on the connection
    cur=con.cursor()
    # Find requested review
    find_review = ("""SELECT text FROM reviews WHERE review_id = '%s';""" % (reviewid))
    # Find reviewed business ID
    find_business = ("""SELECT b.business_id FROM business b, reviews r
        WHERE b.business_id = r.business_id AND r.review_id = '%s';""" % (reviewid))
    positives = 0
    negatives = 0
    toReturn = []

    # Execute query to find review
    cur.execute(find_review)
    # Fetch results in finals array
    text = cur.fetchone()
    print("Original text:")
    print (text)
    print("")
    # Execute query to find business
    cur.execute(find_business)
    business_id = cur.fetchone()
    print("Business ID: %s" %(business_id))
    print("")

    mynum = random.randint(1, 3)

    # Convert tuple to string
    tup = ''.join(text)
    business_id_str = ''.join(business_id)

    def extract_ngrams(text,num):
        toReturn = []
        grams=text.split(' ')
        if num == 1:
            for i in range(len(grams)):
                toReturn.append(grams[i])
        elif num == 2:
            for i in range(len(grams) - 1):
                toReturn.append(grams[i] + ' ' + grams[i+(num-1)])
        elif num == 3:
            for i in range(len(grams) - 2):
                toReturn.append(grams[i] + ' ' + grams[i+1]+' ' + grams[i+2])
        else:
            print("Error when trying to extract n-grams. No valid number given.")
        return(toReturn)

    print("%s-gram splitting:" % (mynum))
    splitted_text = extract_ngrams(tup,mynum)
    print (splitted_text)
    print("")

    # Start counting terms in text
    for gram in splitted_text:

        # Positive terms
        sql_positive = ("""SELECT 1 FROM posterms WHERE '%s' IN (word);""" % (gram))
        cur.execute(sql_positive)
        pos = cur.fetchone()
        if bool(pos) == True:
            positives = positives + mynum
            print("(%s) was found positive" % (gram))

        # Negative terms
        sql_negative = ("""SELECT 1 FROM negterms WHERE '%s' IN (word);""" % (gram))
        cur.execute(sql_negative)
        neg = cur.fetchone()
        if bool(neg) == True:
            negatives = negatives + mynum
            print("(%s) was found negative" % (gram))
    print("")
    print("Positives terms are: %s" % (positives))
    print("Negatives terms are: %s" % (negatives))

    toReturn.append(("Business ID","Review",))
    toReturn.append((business_id_str,tup,))

    result = positives-negatives
    if result > 0:
        toReturn.append(('Comments:', ' Review was found positive.',))
        print('Review was found positive.')
    elif result < 0:
        toReturn.append(('Comments:', ' Review was found negative.',))
        print('Review was found negative.')
    else:
        toReturn.append(('Comments:', ' Cannot conclude if review is positive or negative.'))
        print('Cannot conclude if review is positive or negative.')
    print("")
    cur.close()
    return (toReturn)


def updatezipcode(business_id, zipcode):

    print("Updating zip code in requested business:")

   # Create a new connection
    con=connection()
    # Create a cursor on the connection
    cur=con.cursor()

    # Create the query
    q = ("""SELECT * \
        FROM business b \
        WHERE b.business_id = '%s';""" % (business_id))

    # flag message, preset = ok
    ack = ('OK')

    try:
        # Execute query
        cur.execute(q)
        # Fetch results in results array
        results = cur.fetchall()
    except:
        ack = ('Error')

    if not(results):
        ack = ('Error')
    else:
        updateQuery = ("""UPDATE business SET zip_code = '%s'
        WHERE business_id = '%s';""" % (zipcode, business_id))
        try:
            cur.execute(updateQuery)
        except:
            con.rollback()
            ack = ('Error')

    con.commit()
    print(cur.rowcount, " record(s) affected")
    print("")
    cur.close()
    return [("Result",),(ack,)]

def selectTopNbusinesses(category_id, n):

    print("Select top N businesses:")

    # Create a new connection
    con=connection()
    # Create a cursor on the connection
    cur=con.cursor()
    toReturn = [("Business ID", "Positive Reviews")]

    # Create query
    q = ("""SELECT bc.business_id, COUNT(r.review_id) AS 'Positive Reviews'
        FROM business_category bc , reviews r, reviews_pos_neg rpos
        WHERE bc.category_id = '%s'
        AND bc.business_id = r.business_id
        AND r.review_id = rpos.review_id
        AND rpos.positive = true
        GROUP BY bc.business_id
        ORDER BY count(r.review_id) DESC LIMIT %s;""" % (category_id, n))

    try:
        # Execute query
        cur.execute(q)
        # Fecth all rows in results array
        results = cur.fetchall()
        for row in results:
            toReturn.append(row)
    except:
        print("Error: Unable to fetch data")
        print(toReturn)
        print("")
    cur.close()
    return toReturn

def traceUserInfuence(userId,depth):
    print("Trace user influence:")

    if int(depth) < 1 or int(depth) > 3:
        return [("Invalid depth given",)]

    # -- Main function --
    toReturn = [("User ID",)]
    # Create a new connection
    con=connection()
    # Create a cursor on the connection
    cur=con.cursor()

    # -- Recursive function for multiple depths --
    def recursive(currentId, currentDepth):
        # User friends
        sql_user_friends = """SELECT f.friend_id FROM user u, friends f
            WHERE u.user_id = f.user_id AND u.user_id = '%s';""" % (currentId)
        cur.execute(sql_user_friends)
        friends = cur.fetchall()

        if not friends:
            return [("Requested user has no friends",)]

        # User reviewed businesses
        sql_user_reviewed_businesses = """SELECT b.business_id
            FROM user u, reviews r, business b
            WHERE u.user_id = r.user_id
            AND r.business_id = b.business_id
            AND u.user_id = '%s';""" % (currentId)

        cur.execute(sql_user_reviewed_businesses)
        userReviewedBussinesses = cur.fetchall()

        user_bus_str = ''
        friend_str = ''

        for friend in friends:
            friend_str = ''.join(friend)
            friend_str = friend_str.replace('\'', '')
            # User's friends reviewed businesses
            sql_friend_reviewed_businesses = """SELECT b.business_id
                FROM user u, reviews r, business b
                WHERE u.user_id = r.user_id
                AND r.business_id = b.business_id
                AND u.user_id = '%s';""" % (friend_str)
            sql_user_common_review = """SELECT DISTINCT r.date
                FROM reviews r, business b
                WHERE r.user_id = '%s'
                AND b.business_id = '%s'
                ORDER BY r.date LIMIT 1;""" % (currentId, user_bus_str)
            sql_friend_common_review = """SELECT DISTINCT r.date
                FROM reviews r, business b
                WHERE r.user_id = '%s'
                AND b.business_id = '%s'
                ORDER BY r.date LIMIT 1;""" % (friend_str, user_bus_str)

            cur.execute(sql_friend_reviewed_businesses)
            friendReviewedBusinesses = cur.fetchall()

            for user_bus in userReviewedBussinesses:
                for friend_bus in friendReviewedBusinesses:
                    user_bus_str = ''.join(user_bus)
                    if user_bus == friend_bus:
                        # Find oldest date of user-reviews in common business with friend
                        cur.execute(sql_user_common_review)
                        user_date = cur.fetchone()
                        # Find oldest date of friend-reviews in common business with user
                        cur.execute(sql_friend_common_review)
                        friend_date = cur.fetchone()

                        if user_date < friend_date:
                            # Avoid duplicates
                            if friend not in toReturn:
                                toReturn.append(friend)
                                # Do we need to keep searching?
                                if currentDepth < int(depth):
                                    recursive(friend_str, currentDepth + 1)

    recursive(userId, 1)

    con.close()
    return toReturn
