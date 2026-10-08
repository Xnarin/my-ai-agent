-- Active: 1791247734535@@127.0.0.1@5432@postgres
-- 숙소 예약 ERD 테이블 생성 (PostgreSQL)
-- 참조되는 테이블부터 먼저 만든다: host → accommodation → room, users → 나머지

-- 호스트
CREATE TABLE host (
    host_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT
);

-- 숙소 (호스트 1 : N 숙소)
CREATE TABLE accommodation (
    accommodation_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    host_id INT NOT NULL REFERENCES host(host_id),
    name VARCHAR(100) NOT NULL,
    address VARCHAR(200),
    registration_date DATE,
    description TEXT,
    amenities TEXT  -- 편의시설, 줄바꿈(\n)으로 구분
);

-- 객실 (숙소 1 : N 객실)
CREATE TABLE room (
    room_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    accommodation_id INT NOT NULL REFERENCES accommodation(accommodation_id),
    name VARCHAR(50) NOT NULL,
    cost INT,
    description TEXT,
    status VARCHAR(20)
);

-- 사용자 (user는 PostgreSQL 예약어라 users로 사용)
CREATE TABLE users (
    user_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(100),
    phone_num VARCHAR(20)
);

-- 위시리스트 (숙소 N : M 사용자, 두 FK를 묶어서 PK)
CREATE TABLE wishlist (
    accommodation_id INT REFERENCES accommodation(accommodation_id),
    user_id INT REFERENCES users(user_id),
    PRIMARY KEY (accommodation_id, user_id)
);

-- 리뷰 (사용자 1 : N 리뷰, 객실 1 : N 리뷰)
CREATE TABLE review (
    review_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id),
    room_id INT NOT NULL REFERENCES room(room_id),
    rating INT,
    review_date DATE,
    content TEXT
);

-- 예약 (사용자 1 : N 예약, 객실 1 : N 예약)
CREATE TABLE reservation (
    reservation_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id),
    room_id INT NOT NULL REFERENCES room(room_id),
    check_in_date DATE,
    check_out_date DATE,
    description TEXT,
    status VARCHAR(20),
    people_num INT,
    reservation_date DATE
);
