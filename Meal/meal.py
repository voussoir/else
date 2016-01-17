import datetime
import math
import os
import sqlite3
import sys
import time


UID_CHARACTERS = 16
RECENT_COUNT = 12

STRFTIME = '%Y %m %d %H:%M'

SQL_MEAL_ID = 0
SQL_MEAL_CREATED = 1
SQL_MEAL_HUMAN = 2

SQL_REL_FOOD = 1

SQL_GROUP_FOOD = 0
SQL_GROUP_GROUP = 1

DB_INIT = '''
CREATE TABLE IF NOT EXISTS meals(id TEXT, created INT, human TEXT);
CREATE TABLE IF NOT EXISTS meal_foods(mealid TEXT, food TEXT);
CREATE TABLE IF NOT EXISTS food_groups(food TEXT, foodgroup TEXT);

CREATE INDEX IF NOT EXISTS index_meal_id on meals(id);
CREATE INDEX IF NOT EXISTS index_meal_created on meals(created);
CREATE INDEX IF NOT EXISTS index_food_mealid on meal_foods(mealid);
CREATE INDEX IF NOT EXISTS index_food_food on meal_foods(food);
CREATE INDEX IF NOT EXISTS index_group_food on food_groups(food);
'''.strip()

HELP_TEXT = '''
> meal add pizza, soda     : Add a new meal with the foods "pizza" and "soda".
> meal adjust ec2 +10      : Adjust the timestamp of the meal starting with "ec2" by +10 seconds.
> meal adjust ec2 +10*60   : Adjusting timestamps supports math operations.
> meal group water drinks  : Add "water" to foodgroup "drinks". Used for organization & reports.
> meal group water         : Display the name of the group "water" belongs to.
> meal recent              : Display info and foods for recent meals. Default {recent_count}.
> meal recent 4            : Display the last 4 meals.
> meal recent all          : Display ALL meals.
> meal remove ec2          : Remove the meal whose ID starts with "ec2".
> meal show ec2            : Display info and foods for the meal whose ID starts with "ec2".
> meal ungroup water       : Remove "water" from its foodgroup.
'''.format(recent_count=RECENT_COUNT)

def listget(li, index, fallback=None):
    try:
        return li[index]
    except IndexError:
        return fallback

def uid(length=None):
    '''
    Generate a u-random hex string..
    '''
    if length is None:
        length = UID_CHARACTERS
    identifier = ''.join('{:02x}'.format(x) for x in os.urandom(math.ceil(length / 2)))
    if len(identifier) > length:
        identifier = identifier[:length]
    return identifier


class MealDB():
    def __init__(self, dbname='C:/Git/else/Meal/meal.db'):
        self.dbname = dbname
        self._sql = None
        self._cur = None

    @property
    def sql(self):
        if self._sql is None:
            self._sql = sqlite3.connect(self.dbname)
        return self._sql

    @property
    def cur(self):
        if self._cur is None:
            self._cur = self.sql.cursor()
            statements = DB_INIT.split(';')
            for statement in statements:
                #print(statement)
                self._cur.execute(statement)
        return self._cur

    def add_meal(self, foods=None):
        if foods is None:
            raise Exception('Empty meal!')
        assert isinstance(foods, (list, tuple))
        foods = set(foods)

        if ''.join(foods).replace(' ', '') == '':
            raise Exception('Empty meal!')

        mealid = self.new_uid('meals')
        now = datetime.datetime.now()
        now_stamp = int(now.timestamp())
        now_string = now.strftime(STRFTIME)

        self.normalized_query('INSERT INTO meals VALUES(?, ?, ?)', [mealid, now_stamp, now_string])
        for food in foods:
            self.normalized_query('INSERT INTO meal_foods VALUES(?, ?)', [mealid, food])
        self.sql.commit()
        foods = ', '.join(foods)
        print('Added meal %s at %s with %s' % (mealid, now_string, foods))
        return mealid

    def adjust_timestamp(self, mealid, adjustment):
        '''
        Move a certain meal by `adjustment` seconds. This is useful when you need to
        report a meal that happened a while ago, rather than the current timestamp.
        '''
        meal = self.get_meal_by_id(mealid)
        mealid = meal[SQL_MEAL_ID]
        meal_time = meal[SQL_MEAL_CREATED]
        meal_time += adjustment
        time_string = datetime.datetime.fromtimestamp(meal_time).strftime(STRFTIME)
        self.normalized_query('UPDATE meals SET created=?, human=? WHERE id=?', [meal_time, time_string, mealid])
        self.sql.commit()
        print('Adjusted %s to %s' % (mealid, time_string))

    def normalized_query(self, query, bindings):
        nbindings = []
        for binding in bindings:
            if isinstance(binding, str):
                nbindings.append(binding.lower())
                continue
            nbindings.append(binding)
        self.cur.execute(query, nbindings)

    def get_foods_for_meal(self, mealid):
        meal = self.get_meal_by_id(mealid)
        mealid = meal[SQL_MEAL_ID]
        self.normalized_query('SELECT food FROM meal_foods WHERE mealid == ?', [mealid])
        items = self.cur.fetchall()
        items = [item[0] for item in items]
        return items

    def get_meal_by_id(self, mealid):
        if len(mealid) == UID_CHARACTERS:
            meal_q = mealid
            self.normalized_query('SELECT * FROM meals WHERE id == ?', [meal_q])
        else:
            meal_q = mealid + '%'
            self.normalized_query('SELECT * FROM meals WHERE id LIKE ?', [meal_q])        

        items = self.cur.fetchall()
        if len(items) > 1:
            items = [str(item) for item in items]
            items = '\n'.join(items)
            raise Exception('Found multiple meals for id "%s"\n%s' % (meal_q, items))
        if len(items) == 0:
            raise Exception('Found no meal for id "%s"' % (meal_q))

        meal = items[0]
        return meal

    def group(self, food, groupname):
        '''
        Insert `food` into the foodgroup `groupname`. This is used for organization,
        normalization, and creating dietary reports.
        '''
        self.normalized_query('SELECT * FROM food_groups WHERE food == ?', [food])
        belongs = self.cur.fetchone()

        if groupname is None:
            self.normalized_query('SELECT * FROM food_groups where foodgroup == ?', [food])
            contains = self.cur.fetchall()

            if belongs is not None:
                print('"%s" belongs to group "%s".' % (food, belongs[1]))
            else:
                print('"%s" is not in any group.' % (food))

            if contains is not None and len(contains) > 0:
                contains = [x[0] for x in contains]
                contains = [repr(x) for x in contains]
                contains = ', '.join(contains)
                print('The "%s" group contains: %s' % (food, contains))
            return

        if belongs is not None:
            raise Exception('"%s" is already in group "%s"' % (f[0], f[1]))
        self.normalized_query('INSERT INTO food_groups VALUES(?, ?)', [food, groupname])
        self.sql.commit()
        print('Added "%s" to group "%s"' % (food, groupname))

    def new_uid(self, table):
        '''
        Create a new UID that is unique to the given table.
        '''
        result = None
        query = 'SELECT * FROM {table} WHERE id == ?'.format(table=table)
        while result is None:
            i = uid()
            # Just gotta be sure, man.
            self.normalized_query(query, [i])
            if self.cur.fetchone() is None:
                result = i
        return result

    def remove_meal(self, mealid):
        meal = self.get_meal_by_id(mealid)
        mealid = meal[SQL_MEAL_ID]
        self.normalized_query('DELETE FROM meals WHERE id == ?', [mealid])
        self.normalized_query('DELETE FROM meal_foods WHERE mealid == ?', [mealid])
        self.sql.commit()
        print('Removed meal %s' % (mealid))

    def show_meal(self, mealid):
        '''
        Display:
            id
            timestamp
            foods
        for the meal with the given ID.
        '''
        meal = self.get_meal_by_id(mealid)
        foods = self.get_foods_for_meal(mealid)
        print(meal[SQL_MEAL_ID])
        print(meal[SQL_MEAL_HUMAN])
        foods = ', '.join(foods)
        print(foods)

    def show_recent(self, count=RECENT_COUNT):
        '''
        Display:
            id : timestamp : foods
        for the `count` most recent meals. If count is "all" or "*", show ALL meals.
        '''
        if count in ('all', '*'):
            self.normalized_query('SELECT * FROM meals ORDER BY created DESC', [])
        else:
            self.normalized_query('SELECT * FROM meals ORDER BY created DESC LIMIT ?', [count])
        meals = self.cur.fetchall()
        output = []
        for meal in meals:
            mealid = meal[SQL_MEAL_ID]
            human = meal[SQL_MEAL_HUMAN]
            foods = self.get_foods_for_meal(mealid)
            foods = ', '.join(foods)
            output.append('%s : %s : %s' % (mealid, human, foods))
        output = '\n'.join(output)
        print(output)

    def ungroup(self, food):
        '''
        Remove `food` from whatever group it is in.
        '''
        self.normalized_query('SELECT * FROM food_groups WHERE food == ?', [food])
        f = self.cur.fetchone()
        if f is None:
            raise Exception('"%s" is not part of a group' % (food))
        groupname = f[1]
        self.normalized_query('DELETE FROM food_groups WHERE food == ?', [food])
        self.sql.commit()
        print('Removed "%s" from group "%s"' % (food, groupname))


if __name__ == '__main__':
    mealdb = MealDB()

    args = sys.argv[1:]
    if len(args) == 0:
        command = ''
    else:
        command = args[0].lower()

    if command == 'add':
        args = args[1:]

    elif command == 'adjust':
        mealid = args[1]
        adjustment = args[2]
        adjustment = eval(adjustment)
        mealdb.adjust_timestamp(mealid, adjustment)
        quit()

    elif command == 'group':
        food = args[1]
        groupname = listget(args, 2, None)
        mealdb.group(food, groupname)
        quit()

    elif command == 'recent':
        count = listget(args, 1, RECENT_COUNT)
        mealdb.show_recent(count)
        quit()

    elif command == 'remove':
        mealids = args[1]
        mealids = mealids.replace(' ', '')
        mealids = mealids.split(',')
        for mealid in mealids:
            mealdb.remove_meal(mealid)
        quit()

    elif command == 'show':
        mealid = args[1]
        mealdb.show_meal(mealid)
        quit()

    elif command == 'ungroup':
        food = args[1]
        mealdb.ungroup(food)
        quit()

    else:
        print(HELP_TEXT)
        quit()

    args = ' '.join(args)

    if ';' in args:
        (args, adjustment) = args.split(';')
        adjustment = adjustment.strip()
        adjustment = eval(adjustment)
    else:
        adjustment = 0

    args = args.strip()
    args = args.split(',')
    args = [food.strip() for food in args]
    meal = mealdb.add_meal(args)
    if adjustment != 0:
        mealdb.adjust_timestamp(meal, adjustment)
    quit()