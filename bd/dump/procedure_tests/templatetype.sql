DELETE FROM templatetype;
ALTER TABLE templatetype AUTO_INCREMENT = 1;
CALL usp_templatetype_insert('invoice');
SELECT description = 'invoice' FROM templatetype WHERE id = 1;

CALL usp_templatetype_updateById(1, 'email');
SELECT description = 'email' FROM templatetype WHERE id = 1;

INSERT INTO templatetype VALUES (2, 'invoice');
CALL usp_templatetype_selectAll();

CALL usp_templatetype_selectById(1);
CALL usp_templatetype_selectById(5);

CALL usp_templatetype_selectByDescription('email');
CALL usp_templatetype_selectByDescription('ajskdjaskd');
