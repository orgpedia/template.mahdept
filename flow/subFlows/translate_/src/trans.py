import json
import sys
from pathlib import Path

from google.cloud import translate_v2 as translate



INDIC = {
    "Assamese": "as",
    "Bengali": "bn",
    "Gujarati": "gu",
    "Hindi": "hi",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Marathi": "mr",
    "Odia": "or",
    "Punjabi": "pa",
    "Tamil": "ta",
    "Telugu": "te",
}


def load_translations():
    indic2en_trans = {}
    trans_file = Path("conf") / 'trans.json'
    if trans_file.exists():
        json_list = json.loads(trans_file.read_text())
        for trans_dict in json_list:
            m, e = trans_dict['mr'], trans_dict['en']
            indic2en_trans[m] = e
    return indic2en_trans

def save_translations(indic2en_trans):
    output_file = Path("conf") / 'trans.json'
    save_trans = sorted([{'mr': k, 'en': v} for (k, v) in indic2en_trans.items()], key=lambda d: d['mr'])
    output_file.write_text(json.dumps(save_trans, indent=2, ensure_ascii=False))

def get_para_info(p, indic2en_trans):
    return {'page_idx': p['page_idx'],
            'para_idx': p['para_idx'],
            'mr': p['text'],
            'en': indic2en_trans[p['text']]
            }

def get_table_info(t, indic2en_trans):
    row_trans = []
    for row in t['rows']:
        cells_trans = []
        for cell in get_cells(row):
            if is_number(cell):
                cells_trans.append(trans_number(cell))
            else:
                cells_trans.append(indic2en_trans[cell])
        trans_text = f'|{"|".join(cells_trans)}|'
        row_trans.append({'mr': row, 'en': trans_text})
    return {
        'page_idx': t['page_idx'],
        'table_idx': t['table_idx'],
        'rows': row_trans,
    }

BatchSize = 100
def gcp_translate(texts, gcp_client, indic2en_trans):
    if not texts:
        return []

    texts = set(texts)
    texts = [ t for t in texts if t not in indic2en_trans ]
    for start in range(0, len(texts), BatchSize):
        texts_batch = texts[start:start+BatchSize]

        trans_dicts = gcp_client.translate(texts_batch,
                                           source_language='mr',
                                           target_language='en')

        trans = [t['translatedText'] for t in trans_dicts]
        
        for (txt, trn) in zip(texts_batch, trans):
            indic2en_trans[txt] = trn

        save_translations(indic2en_trans)
    return trans
    

def translate_texts(texts, lang, indic2en_model, indic2en_trans):
    if not texts:
        return []

    indic = INDIC[lang]
    texts = set(texts)
    
    texts = [ t for t in texts if t not in indic2en_trans ]
    for start in range(0, len(texts), BatchSize):
        texts_batch = texts[start:start+BatchSize]
        
        trans = [indic2en_model.translate_paragraph(text, indic, 'en') for text in texts_batch]
        
        for (txt, trn) in zip(texts_batch, trans):
            indic2en_trans[txt] = trn

        save_translations(indic2en_trans)
    return trans


def get_cells(row):
    return row.strip('|').split('|')

MarathiNums = '१२३४५६७८९०.() '
def is_number(cell):
    cell = cell.strip('.) ')
    return all(c in MarathiNums for c in cell)

EnglishNums = '1234567890.() '
MarthiEnglishNumDict = dict( (m,e) for (m, e) in zip(MarathiNums, EnglishNums))
def trans_number(cell):
    return ''.join(MarthiEnglishNumDict[c] for c in cell)

UseGCP = True
if __name__ == '__main__':
    input_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    
    indic2en_trans = load_translations()
    
    # Read parafinder files
    para_translate, cell_translate = [], []
    for json_path in input_dir.glob('*.pdf.parafinder.json'):
        try:
            jd = json.loads(json_path.read_text())
        except:
            print(f'FAILED: {json_path}')
            continue

        para_translate += [p['text'] for p in jd['para_infos'] if p['text'] not in indic2en_trans]

        for row in [r for t in jd['table_infos'] for r in t['rows']]:
            cells = get_cells(row)
            cells = [c for c in cells if not is_number(c)] # skip numbers as they are jumbled
            cell_translate += [ c for c in cells if c not in indic2en_trans]

    para_translate, cell_translate = set(list(para_translate)), set(list(cell_translate))        
    print(f'Translating #para: {len(para_translate)} #cells: {len(cell_translate)}')

    # translate para & cell
    if para_translate or cell_translate:
        if UseGCP:
            # Set up the Google Cloud Translate API client
            translate_client = translate.Client()
            gcp_translate(para_translate, translate_client, indic2en_trans)
            gcp_translate(cell_translate, translate_client, indic2en_trans)            
        else:
            from fairseq import checkpoint_utils, distributed_utils, options, tasks, utils    
            from inference.engine import Model
            indic2en_model = Model(expdir='indic-en')
        
            translate_texts(para_translate, "Marathi", indic2en_model, indic2en_trans)
            translate_texts(cell_translate, "Marathi", indic2en_model, indic2en_trans)    

    #end if

    # write the paratrans files
    for json_path in input_dir.glob('*.pdf.parafinder.json'):
        try:
            jd = json.loads(json_path.read_text())
        except:
            print(f'FAILED: {json_path}')
            continue

        para_infos = [get_para_info(p, indic2en_trans) for p in jd['para_infos'] ]
        table_infos = [get_table_info(t, indic2en_trans) for t in jd['table_infos'] ]

        trans_infos = {'para_infos': para_infos,
                       'table_infos': table_infos,
                       'table_para_idxs_infos': jd['table_para_idxs_infos'],
                       }

        output_path = output_dir / json_path.name.replace('parafinder', 'paratrans')
        output_path.write_text(json.dumps(trans_infos, indent=2, ensure_ascii=False))
        
        

                  

        

