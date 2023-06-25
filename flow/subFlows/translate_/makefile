.DEFAULT_GOAL := all

.PHONY: all

input/doc_translations_todo.json:
	cd input && ln -sf ../../../writeTxt_/output/doc_translations_todo.json .
	test -f ../../writeTxt_/output/doc_translations_todo.json.gz && gunzip ../../writeTxt_/output/doc_translations_todo.json.gz

output/doc_translations.json:
	cd output && ln -sf ../../../writeTxt_/conf/doc_translations.json .
	test -f ../../writeTxt_/conf/doc_translations.json.gz && gunzip ../../writeTxt_/conf/doc_translations.json.gz


all: input/doc_translations_todo.json output/doc_translations.json
	poetry run python src/translate.py input output > logs/trans.log

compress:
	test -f ../../writeTxt_/output/doc_translations_todo.json && gzip ../../writeTxt_/output/doc_translations_todo.json
	test -f ../../writeTxt_/conf/doc_translations.json && gzip ../../writeTxt_/conf/doc_translations.json
