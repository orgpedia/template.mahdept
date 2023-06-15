import sys
from operator import attrgetter
from pathlib import Path



import docint
import orgpedia

import para_finder

if __name__ == '__main__':
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    viz = docint.load('src/writeTxt.yml')

    if input_path.is_dir():
        assert output_path.is_dir()
        input_files = sorted(input_path.glob('*.pdf'), key=attrgetter('name'))
        print(len(input_files))

        docs = viz.pipe_all(input_files)

        for doc in docs:
            output_doc_path = output_path / (doc.pdf_name + '.doc.json')
            doc.to_disk(output_doc_path) 
    elif input_path.suffix.lower() == '.pdf':
        doc = viz(input_path)
        doc.to_disk(output_path)        

    elif input_path.suffix.lower() in ('.list', '.lst'):
        print('processing list')
        input_files = input_path.read_text().split('\n')
        
        pdf_files = [Path('input') / f for f in input_files if f and f[0] != '#']
        pdf_files = [p for p in pdf_files if p.exists()]

        docs = viz.pipe_all(pdf_files)
        for doc in docs:
            output_doc_path = output_path / (doc.pdf_name + '.doc.json')
            doc.to_disk(output_doc_path)
        
        
        
        

