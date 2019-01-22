USE photoshare_data;

CREATE TABLE Users (
    user_id int4  AUTO_INCREMENT,
    email varchar(255) UNIQUE,
    psswrd varchar(255) NOT NULL,
    fname varchar(255) DEFAULT "John", 
    lname varchar(255) DEFAULT "Doe", 
    username char(35) UNIQUE, 
    dob date NOT NULL, 
    p_pic longblob,
    bio text, 
    hometown varchar(255) DEFAULT "None given",
    gender char(10) DEFAULT "None given", 
    contribution int DEFAULT 0,
  CONSTRAINT users_pk PRIMARY KEY (user_id)
);

CREATE TABLE Usernames(
	next_available int AUTO_INCREMENT PRIMARY KEY
);

DELIMITER |
CREATE TRIGGER assign_default_username BEFORE INSERT ON Users FOR EACH ROW BEGIN
DECLARE next_number int;
INSERT INTO Usernames VALUES();
SET next_number = (SELECT next_available FROM Usernames ORDER BY next_available DESC LIMIT 1);
IF NEW.username IS NULL THEN 
SET NEW.username = CONCAT(NEW.fname, NEW.lname, next_number);
END IF; END |
DELIMITER ;

CREATE TABLE Friends(
	user1_id int4 NOT NULL,
    user2_id int4 NOT NULL, 
    CONSTRAINT friendship PRIMARY KEY (user1_id, user2_id), 
    FOREIGN KEY (user1_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (user2_id) REFERENCES Users(user_id) ON DELETE CASCADE
);


CREATE TABLE Albums(
	album_id int AUTO_INCREMENT, 
    user_id int4 NOT NULL, 
    album_name varchar(255) DEFAULT " ", 
    creation_date datetime DEFAULT CURRENT_TIMESTAMP,
    INDEX owner_index (user_id),
    UNIQUE INDEX user_album_unique_name (user_id, album_name),
    CONSTRAINT album_pk PRIMARY KEY (album_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);


CREATE TABLE Pictures(
  picture_id int4 AUTO_INCREMENT,
  imgdata longblob NOT NULL,
  user_id int4 NOT NULL,
  album_id int4 NOT NULL, 
  caption VARCHAR(255),
  INDEX owner_index (user_id),
  FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (album_id) REFERENCES Albums(album_id) ON DELETE CASCADE,
  CONSTRAINT pictures_pk PRIMARY KEY (picture_id)
);

CREATE TABLE Comments(
	comment_id int AUTO_INCREMENT, 
    user_id int4 NOT NULL, 
    picture_id int4 NOT NULL, 
    picture_text text, 
    posted datetime DEFAULT CURRENT_TIMESTAMP, 
    INDEX commenter_id (user_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE, 
    FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE, 
    CONSTRAINT comment_pk PRIMARY KEY (comment_id)
);

DELIMITER | 
CREATE TRIGGER before_posting_comment BEFORE INSERT ON Comments 
FOR EACH ROW BEGIN 
IF (NEW.user_id = (SELECT user_id FROM Pictures WHERE
	NEW.picture_id = Pictures.picture_id)) THEN 
    SIGNAL SQLSTATE '01500'
      SET MESSAGE_TEXT = 'Cannot comment on image if oneself owns it', MYSQL_ERRNO = 1500;
END IF; END |
DELIMITER ;  


CREATE TABLE Tags(
	picture_id int4, 
    tag_name char(25), 
    CONSTRAINT picture_and_tag PRIMARY KEY (picture_id, tag_name), 
    FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE
);

CREATE TABLE Likes(
	picture_id int4,
    user_id int4,
    CONSTRAINT like_pk PRIMARY KEY (picture_id, user_id), 
    FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE, 
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);