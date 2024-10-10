import asyncpg as pg
import os


async def sql_start():
    global conn, cur
    conn = await pg.connect(
        host=os.environ['HOST'],
        database=os.environ['DATABASE'],
        user=os.environ['USER'],
        password=os.environ['DB_PASS'],
        port=os.environ['DB_PORT']
    )
    cur = conn


async def sql_close():
    conn.close()


async def sql_find_jobs(user_id, job_title):
    await sql_start()
    async with cur.transaction():
        query = """
            WITH
                USER_COUNTRY AS (
                    SELECT
                        COUNTRY
                    FROM
                        PUBLIC.COUNTRY_BY_USER
                    WHERE
                        USER_ID = $1
                    LIMIT
                        1
                )
            SELECT
                LINKS.RESOURCE_NAME,
                LINKS.URL,
                LINKS.SEPARATOR,
                COUNTRIES.COUNTRY,
                COUNTRIES.COUNTRY_SECOND_NAME
            FROM
                PUBLIC.LINKS_TO_FIND_JOB_BY_COUNTRY AS LINKS
                LEFT JOIN PUBLIC.COUNTRY_DATA AS COUNTRIES ON (
                LINKS.COUNTRY =	COUNTRIES.COUNTRY)
            WHERE
                LINKS.COUNTRY IN (
                        SELECT
                            COUNTRY
                        FROM
                            USER_COUNTRY
                    )
                OR LINKS.COUNTRY = 'all';
            """
        result = await cur.fetch(query, user_id)
    await sql_close()
    links = {}
    for row in result:
        job = job_title.replace(" ", row['separator'])
        title = row['resource_name']
        link = row['url']
        link = link.format(location=row['country'], brief_location=row['country_second_name'], job_title=job)
        if title and link is not None:
            links.update({title: link})
    if len(result) != 0:
        return links
    else:
        return ""


async def sql_get_user_country(user_id):
    await sql_start()
    query = 'SELECT country FROM country_by_user WHERE user_id = $1'
    result = await cur.fetch(query, user_id)
    await sql_close()
    if len(result) != 0:
        return result[0]['country']
    else:
        return ""


async def sql_find_links():
    await sql_start()
    async with cur.transaction():
        query = "SELECT resource_name, url FROM useful_links"
        result = await cur.fetch(query)
        links = {}
        for i in result:
            title = i[0]
            link = i[1]
            if title and link is not None:
                links.update({title: link})
    await sql_close()
    return links


async def sql_find_rent(user_id):
    await sql_start()
    async with cur.transaction():
        query = """
            WITH user_country AS (
                SELECT country
                FROM public.country_by_user
                WHERE user_id = $1
                LIMIT 1
            )
            SELECT resource_name, url
            FROM public.links_for_rent
            WHERE country IN (SELECT country FROM user_country) or country = 'all';
            """
        result = await cur.fetch(query, user_id)
        await sql_close()
        if len(result) != 0:
            links = {}
            for row in result:
                title = row['resource_name']
                link = row['url']
                if title and link is not None:
                    links.update({title: link})
            return links
        else:
            return ""


async def sql_send_feedback(message_text):
    await sql_start()
    async with cur.transaction():
        query = 'INSERT INTO feedback (message) VALUES ($1)'
        await cur.execute(query, message_text)
    await sql_close()


async def get_country_with_data(country, user_id):
    await sql_start()
    async with cur.transaction():
        query = """ 
        WITH closest_country AS (
            SELECT country, img, capital, largest_city, official_languages, common_languages, currency, time_zone, 
            calling_code, population, net_migration, gdp_per_capita, gdp_growth, unemployment, inflation, co2_emissions, 
            access_to_electricity, electricity_production, access_to_internet, gpi, total_score_and_status, 
            political_rights, civil_liberties, pfi, hdi, cpi
            FROM country_data
            ORDER BY 
                LEAST(
                    levenshtein(country, $1),
                    levenshtein(country_second_name, $1),
                    levenshtein(country_third_name, $1)
                ) ASC
            LIMIT 1
        ), user_update AS (
            UPDATE country_by_user AS cbu
            SET country = cc.country
            FROM closest_country AS cc
            WHERE cbu.user_id = $2
            AND cbu.country IS NOT NULL
            RETURNING cbu.user_id
        ), user_insert AS (
            INSERT INTO country_by_user(country, user_id)
            SELECT cc.country, $3
            FROM closest_country AS cc
            WHERE NOT EXISTS (
                SELECT 1
                FROM user_update
            )
            RETURNING user_id
        )
        SELECT *
        FROM closest_country;
        """

        result = await cur.fetch(query, country, user_id, user_id)
        data = ""
        img = ""
        if len(result) != 0:
            for row in result:
                country = row['country']
                img = row['img']
                data = "*" + country.title() + "*\n" + "*Main info:*" + "\n"
                if row['largest_city'] != "":
                    data = data + "Largest city: " + row['largest_city'].title() + "\n"
                if row['official_languages'] != "":
                    data = data + "Official languages: " + row['official_languages'].title() + "\n"
                if row['common_languages'] != "":
                    data = data + "Common languages: " + row['common_languages'].title() + "\n"
                if row['currency'] != "":
                    data = data + "Currency: " + row['currency'].title() + "\n"
                if row['time_zone'] != "":
                    data = data + "Time zone: " + row['time_zone'].title() + "\n"
                if row['calling_code'] != "":
                    data = data + "Calling code: " + row['calling_code'].title() + "\n"
                if row['population'] != "":
                    data = data + "Population: " + row['population'].title() + "\n"
                if row['net_migration'] != "":
                    data = data + "Net migration (number of immigrants - number of emigrants): " + row[
                        'net_migration'].title() + "\n"
                if row['gdp_per_capita'] != "":
                    data = data + "Gdp per capita: " + row['gdp_per_capita'].title() + "\n"
                if row['gdp_growth'] != "":
                    data = data + "Gdp growth: " + row['gdp_growth'].title() + "\n"
                if row['unemployment'] != "":
                    data = data + "Unemployment (% of total labor force): " + row['unemployment'].title() + "\n"
                if row['inflation'] != "":
                    data = data + "Inflation (annual %): " + row['inflation'].title() + "\n"
                if row['co2_emissions'] != "":
                    data = data + "CO2 emissions (metric tons per capita): " + row['co2_emissions'].title() + "\n"
                if row['access_to_electricity'] != "":
                    data = data + "Access to electricity (% of population): " + row[
                        'access_to_electricity'].title() + "\n"
                if row['electricity_production'] != "":
                    data = data + ("Electricity production from renewable sources, excluding hydroelectric (% of "
                                   "total): ") + \
                           row['electricity_production'].title() + "\n"
                if row['access_to_internet'] != "":
                    data = data + "Individuals using the Internet (% of population): " + row[
                        'access_to_internet'].title() + "\n"
                if row['gpi'] != "":
                    data = data + "Global piece index: " + row['gpi'].title() + "\n"
                if row['total_score_and_status'] != "":
                    data = data + "Freedom score: " + row['total_score_and_status'].title() + "\n"
                if row['political_rights'] != "":
                    data = data + "Political rights: " + row['political_rights'].title() + "\n"
                if row['civil_liberties'] != "":
                    data = data + "Civil liberties: " + row['civil_liberties'].title() + "\n"
                if row['pfi'] != "":
                    data = data + "Press freedom index: " + row['pfi'].title() + "\n"
                if row['hdi'] != "":
                    data = data + "Human Development Index: " + row['hdi'].title() + "\n"
                if row['cpi'] != "":
                    data = data + "Corruption Perceptions Index: " + row['cpi'].title() + "\n"

    await sql_close()

    return data, img


async def sql_find_climate(user_id):
    await sql_start()
    async with cur.transaction():
        query = """
        WITH user_country AS (
            SELECT country
            FROM public.country_by_user
            WHERE user_id = $1
            LIMIT 1
        )
        SELECT COALESCE(climate, '') AS climate
        FROM public.country_data
        WHERE country IN (SELECT country FROM user_country);
        """
        result = await cur.fetch(query, user_id)
    await sql_close()
    if len(result) != 0:
        return result[0]['climate'].replace('\\n', '\n')
    else:
        return ""


async def sql_find_taxes(user_id):
    await sql_start()
    async with cur.transaction():
        query = """
        WITH user_country AS (
            SELECT country
            FROM public.country_by_user
            WHERE user_id = $1
            LIMIT 1
        )
        SELECT COALESCE(taxes, '') AS taxes
        FROM public.country_data
        WHERE country IN (SELECT country FROM user_country);
        """
        result = await cur.fetch(query, user_id)
    await sql_close()
    if len(result) != 0:
        return result[0]['taxes'].replace('\\n', '\n')
    else:
        return ""


async def sql_find_expanses(user_id):
    await sql_start()
    async with cur.transaction():
        query = """
        WITH user_country AS (
            SELECT country
            FROM public.country_by_user
            WHERE user_id = $1
            LIMIT 1
        )
        SELECT COALESCE(expanses, '') AS expanses
        FROM public.country_data
        WHERE country IN (SELECT country FROM user_country);
        """
        result = await cur.fetch(query, user_id)
    await sql_close()
    if len(result) != 0:
        return result[0]['expanses'].replace('\\n', '\n')
    else:
        return ""


async def sql_find_main_cities(user_id):
    await sql_start()
    async with cur.transaction():
        query = """
        WITH user_country AS (
            SELECT country
            FROM public.country_by_user
            WHERE user_id = $1
            LIMIT 1
        )
        SELECT COALESCE(main_cities, '') AS main_cities
        FROM public.country_data
        WHERE country IN (SELECT country FROM user_country);
        """
        result = await cur.fetch(query, user_id)
    await sql_close()
    if len(result) != 0:
        return result[0]['main_cities'].replace('\\n', '\n')
    else:
        return ""
