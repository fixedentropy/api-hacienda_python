SET FOREIGN_KEY_CHECKS = 0;
DELETE FROM template;
ALTER TABLE template AUTO_INCREMENT = 1;
CALL usp_template_insert(
	1,
	NULL,
	'somedata'
);
SELECT idtemplatetype = 1,
	idcompany IS NULL,
	`data` = 'somedata'
FROM template
WHERE id = 1;

CALL usp_template_updateById(1, 2, 1, '');
SELECT idtemplatetype <> 1,
	idcompany IS NOT NULL,
	`data` <> 'somedata'
FROM template
WHERE id = 1;

CALL usp_template_deleteById(1);
SELECT COUNT(*) = 0 FROM template;

INSERT INTO template
VALUES (
	1,
	1,
	NULL,
	'somedata'
), (
	2,
	1,
	1,
	'otherdata'
);

CALL usp_template_selectCommon(NULL); -- one result
CALL usp_template_selectCommon(1); -- one result
CALL usp_template_selectCommon(5); -- no results

CALL usp_template_selectById(2); -- one result
CALL usp_template_selectById(5); -- no results

CALL usp_template_selectByUQ_Template(1, 1); -- one result

CALL usp_template_selectByTemplateType(1); -- two result
CALL usp_template_selectByTemplateType(6); -- no results

CALL usp_template_selectByCompany(1); -- one result
CALL usp_template_selectByCompany(6); -- no results

CALL usp_template_getDataById(1); -- one result
CALL usp_template_getDataById(2); -- one result
CALL usp_template_getDataById(3); -- no result

SET FOREIGN_KEY_CHECKS = 1;
