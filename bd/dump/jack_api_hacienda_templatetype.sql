CREATE TABLE templatetype (
    id TINYINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    description VARCHAR(50) NOT NULL,
    CONSTRAINT UQ_TemplateType UNIQUE (description)
);
INSERT INTO templatetype (id, description)
VALUES (1, 'email');
