import os
import psycopg2
from psycopg2.extras import RealDictCursor

_DEGREE_ALIASES = {
    "b.tech": ["b.tech", "btech", "bachelor of technology"],
    "btech": ["b.tech", "btech", "bachelor of technology"],
    "bachelor of technology": ["b.tech", "btech", "bachelor of technology"],
    "be": ["be", "b.e", "b.e.", "bachelor of engineering"],
    "b.e": ["be", "b.e", "b.e.", "bachelor of engineering"],
    "b.e.": ["be", "b.e", "b.e.", "bachelor of engineering"],
    "bachelor of engineering": ["be", "b.e", "b.e.", "bachelor of engineering"],
    "b.sc": ["b.sc", "bsc", "bachelor of science"],
    "bsc": ["b.sc", "bsc", "bachelor of science"],
    "bachelor of science": ["b.sc", "bsc", "bachelor of science"],
    "bca": ["bca", "bachelor of computer application", "bachelor of computer applications"],
    "bachelor of computer application": ["bca", "bachelor of computer application"],
    "m.tech": ["m.tech", "mtech", "master of technology"],
    "mtech": ["m.tech", "mtech", "master of technology"],
    "master of technology": ["m.tech", "mtech", "master of technology"],
    "mca": ["mca", "master of computer application", "master of computer applications"],
    "master of computer application": ["mca", "master of computer application"],
    "mba": ["mba", "master of business administration"],
    "master of business administration": ["mba", "master of business administration"],
    "m.sc": ["m.sc", "msc", "master of science"],
    "msc": ["m.sc", "msc", "master of science"],
    "master of science": ["m.sc", "msc", "master of science"],
    "phd": ["phd", "ph.d", "ph.d.", "doctor of philosophy"],
    "ph.d": ["phd", "ph.d", "ph.d.", "doctor of philosophy"],
}


def get_conn():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return psycopg2.connect(database_url)


def add_candidate(file_name, name, email, phone, raw_text, skills, education):
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO candidates (file_name, name, email, phone, raw_text)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (file_name, name, email, phone, raw_text),
                )
                candidate_id = cur.fetchone()[0]

                for skill_name, category in skills or []:
                    cur.execute(
                        """
                        INSERT INTO skills (name, category)
                        VALUES (%s, %s)
                        ON CONFLICT (name) DO UPDATE SET category = EXCLUDED.category
                        RETURNING id
                        """,
                        (skill_name, category),
                    )
                    skill_id = cur.fetchone()[0]
                    cur.execute(
                        """
                        INSERT INTO candidate_skills (candidate_id, skill_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (candidate_id, skill_id),
                    )

                for edu in education or []:
                    cur.execute(
                        """
                        INSERT INTO education (candidate_id, degree, institution)
                        VALUES (%s, %s, %s)
                        """,
                        (candidate_id, edu.get("degree"), edu.get("institution")),
                    )
        return candidate_id
    finally:
        conn.close()


def get_candidate(candidate_id):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, file_name, name, email, phone, raw_text, created_at
                FROM candidates
                WHERE id = %s
                """,
                (candidate_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            candidate = dict(row)

            cur.execute(
                """
                SELECT s.name, s.category
                FROM skills s
                JOIN candidate_skills cs ON cs.skill_id = s.id
                WHERE cs.candidate_id = %s
                ORDER BY s.category, s.name
                """,
                (candidate_id,),
            )
            candidate["skills"] = [dict(r) for r in cur.fetchall()]

            cur.execute(
                """
                SELECT degree, institution
                FROM education
                WHERE candidate_id = %s
                ORDER BY id
                """,
                (candidate_id,),
            )
            candidate["education"] = [dict(r) for r in cur.fetchall()]
            return candidate
    finally:
        conn.close()


def search_candidates(name=None, skills=None, degree=None):
    conditions = []
    params = []

    if name and name.strip():
        conditions.append("c.name ILIKE %s")
        params.append(f"%{name.strip()}%")

    clean_skills = list(
        dict.fromkeys(s.strip().lower() for s in (skills or []) if s and s.strip())
    )
    if clean_skills:
        conditions.append(
            """
            c.id IN (
                SELECT cs.candidate_id
                FROM candidate_skills cs
                JOIN skills s ON s.id = cs.skill_id
                WHERE LOWER(s.name) = ANY(%s)
                GROUP BY cs.candidate_id
                HAVING COUNT(DISTINCT LOWER(s.name)) = %s
            )
            """
        )
        params.append(clean_skills)
        params.append(len(clean_skills))

    if degree and degree.strip():
        term = degree.strip().lower()
        patterns = [f"%{p}%" for p in _DEGREE_ALIASES.get(term, [term])]
        conditions.append(
            """
            EXISTS (
                SELECT 1
                FROM education e
                WHERE e.candidate_id = c.id AND e.degree ILIKE ANY(%s)
            )
            """
        )
        params.append(patterns)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT c.id, c.file_name, c.name, c.email, c.phone, c.created_at
                FROM candidates c
                {where_clause}
                ORDER BY c.created_at DESC, c.id DESC
                """,
                params,
            )
            candidates = [dict(r) for r in cur.fetchall()]
            if not candidates:
                return []

            ids = [c["id"] for c in candidates]
            by_id = {c["id"]: c for c in candidates}
            for c in candidates:
                c["skills"] = []
                c["education"] = []

            cur.execute(
                """
                SELECT cs.candidate_id, s.name, s.category
                FROM candidate_skills cs
                JOIN skills s ON s.id = cs.skill_id
                WHERE cs.candidate_id = ANY(%s)
                ORDER BY s.category, s.name
                """,
                (ids,),
            )
            for r in cur.fetchall():
                by_id[r["candidate_id"]]["skills"].append(
                    {"name": r["name"], "category": r["category"]}
                )

            cur.execute(
                """
                SELECT candidate_id, degree, institution
                FROM education
                WHERE candidate_id = ANY(%s)
                ORDER BY id
                """,
                (ids,),
            )
            for r in cur.fetchall():
                by_id[r["candidate_id"]]["education"].append(
                    {"degree": r["degree"], "institution": r["institution"]}
                )

            return candidates
    finally:
        conn.close()


def delete_candidate(candidate_id):
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM candidates WHERE id = %s RETURNING id",
                    (candidate_id,),
                )
                return cur.fetchone() is not None
    finally:
        conn.close()
