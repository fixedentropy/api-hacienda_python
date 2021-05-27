CREATE TABLE template (
	id INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
	idtemplatetype TINYINT UNSIGNED NOT NULL,
	idcompany INT,
	`data` MEDIUMBLOB NOT NULL,
	CONSTRAINT UQ_Template UNIQUE (idtemplatetype, idcompany),
	CONSTRAINT FK_Template_TemplateType FOREIGN KEY (idtemplatetype) REFERENCES templatetype (id),
	CONSTRAINT FK_Template_Company FOREIGN KEY (idcompany) REFERENCES companies (id)
);
INSERT INTO template (id, idtemplatetype, idcompany, `data`)
VALUES (1, 1, NULL, '');

