.DEFAULT_GOAL := all

input/doc_translations_todo.json:
	cd input && ln -s ../../../writeTxt_/output/doc_translations_todo.json .

output/doc_translations.json:
	cd output && ln -s ../../../writeTxt_/conf/doc_translations.json .


all: input/doc_translations_todo.json output/doc_translations.json
	poetry run python src/translate.py input output > logs/trans.log
