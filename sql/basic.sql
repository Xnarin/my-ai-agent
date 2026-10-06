-- ctrl + enter
CREATE DATABASE demodb;

-- 기본적인 테이블 생성
CREATE TABLE student (
    id VARCHAR(7) PRIMARY KEY,
    name VARCHAR(10),
    grade INT,
    major VARCHAR(20)
);

-- 외래키가 있는 테이블 생성
CREATE TABLE attendance (
    attendance_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_id VARCHAR(7) REFERENCES student(id),
    date DATE,
    status VARCHAR(10)
);

ALTER TABLE student
ADD phone VARCHAR(20);

ALTER TABLE student
DROP COLUMN phone;

DROP DATABASE demodb;

INSERT INTO student (id, name, grade, major)
VALUES ('2024001', '김철수', 1, '컴퓨터공학');

INSERT INTO student VALUES
    ('2024002', '이영희', 2, '경영학'),
    ('2024003', '박민수', 3, '물리학');


    SELECT * FROM student;

    SELECT student.id, student.name FROM student;

    SELECT * FROM student WHERE grade = 2;

    UPDATE student
SET  major = '컴공';

DELETE FROM student;