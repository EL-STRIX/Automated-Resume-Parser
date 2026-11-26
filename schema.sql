CREATE TABLE candidates (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    raw_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE skills (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL
);

CREATE TABLE candidate_skills (
    candidate_id INT NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    skill_id INT NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    PRIMARY KEY (candidate_id, skill_id)
);

CREATE TABLE education (
    id SERIAL PRIMARY KEY,
    candidate_id INT NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    degree VARCHAR(100),
    institution VARCHAR(255)
);

-- Indexes for search
CREATE INDEX idx_candidates_name ON candidates (LOWER(name));
CREATE INDEX idx_candidate_skills_skill ON candidate_skills (skill_id);
CREATE INDEX idx_education_degree ON education (LOWER(degree));
CREATE INDEX idx_education_candidate ON education (candidate_id);
