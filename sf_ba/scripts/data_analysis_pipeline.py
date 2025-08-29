import ast
import statistics
from preprocess_annotation_into_dictionary import convert_files_to_dict
from dict_to_smatch_format_conversion import create_smatch_formatted_annotations, organize_in_blocks
from score_calculation import calculate_scores

# 0. BACL configuration:

languages = ['de', 'lt', 'sr']
annotators = ['ann1', 'ann2', 'ann3']
annotation_abbreviations = ['de_ann1', 'de_ann2', 'de_ann3', 'lt', 'sr']
annotated_structures_dir = 'input_files/annotated'
empty_structures_dir = 'input_files/empty'
input_sentence_alignment_filepath = 'sentence_alignments/sentence_alignment_dict.txt'
files_for_score_dir = 'files_for_score'
output_filepath_for_scores = 'score_outputs.txt'
annotated_german_files_dict = {
    'ann1': [0,1,2,4,5,9],
    'ann2': [0,1,2,3,6,7,10],
    'ann3': [3,5,7,8,9,10]
}

param_combinations = ['0000', '1111', '1000', '0100', '0010', '0001'] # insert relevant combinations here
number_of_blocks = 11
block_size = 50
leading_language = languages[0] # 'de'

## 1. Open all relevant input data (sentence alignment, cusf files with and wihtout annotations):

# sentence alignment file:
with open(input_sentence_alignment_filepath, 'r') as f:
    sentence_alignment = f.read()
    sentence_alignment = ast.literal_eval(sentence_alignment)

# empty structures data:
empty_structures = {}
for language in languages:
    with open(f'{empty_structures_dir}/{language}_empty.cusf') as empty_annotation_file:
        empty_structure = ''
        for line in empty_annotation_file:
            empty_structure += line
        empty_structures[language] = empty_structure

# annotated structures data:
annotated_structures = {}
for annotation_abbreviation in annotation_abbreviations:
    with open(f'{annotated_structures_dir}/{annotation_abbreviation}.cusf') as annotated_file:
        annotated_structure = ''
        for line in annotated_file:
            annotated_structure += line
        annotated_structures[annotation_abbreviation] = annotated_structure  

annotation_data = {
    'empty': {'cusf': empty_structures},
    'annotated': {'cusf': annotated_structures}
}


## 2. Create and save python dictionaries for empty and annotated structures:
for structure_type in annotation_data:
    current_dict = convert_files_to_dict(annotation_data[structure_type]['cusf'],sentence_alignment)
    annotation_data[structure_type]['dict'] = current_dict
    with open(f'analysis_dictionaries/{structure_type}_structures_dict.txt', 'w') as output_dict_file:
        print(current_dict, file=output_dict_file)

    ## 3. Create smatch readable (AMR) files for empty and annotated structures:
    annotation_data[structure_type]['AMR'] = {}
    
    if structure_type == 'annotated':
        for param_combination in param_combinations:
            annotation_data[structure_type]['AMR'][f'params{param_combination}'] = {}
            current_AMRs = create_smatch_formatted_annotations(current_dict,param_combination)
            annotation_data[structure_type]['AMR'][f'params{param_combination}']['all'] = current_AMRs  
            annotation_data[structure_type]['AMR'][f'params{param_combination}']['blocks'] = organize_in_blocks(current_AMRs, sentence_alignment, leading_language, number_of_blocks, block_size, files_for_score_dir, f'params{param_combination}')

    if structure_type == 'empty':
        annotation_data[structure_type]['AMR']['no_params'] = {}
        current_AMRs = create_smatch_formatted_annotations(current_dict)
        annotation_data[structure_type]['AMR']['no_params']['all'] = current_AMRs
        annotation_data[structure_type]['AMR']['no_params']['blocks'] = organize_in_blocks(current_AMRs, sentence_alignment, leading_language, number_of_blocks, block_size, files_for_score_dir)


## 4. Calculate scores for
## - for each parameter combination:
## a) crosslingual Smatch score (lt-sr, de-lt, de-sr)
## a.!!) for de, average score of all annotators needs to be calculated
## b) interannotator Smatch score (only for German)
## c) empty vs annotated structures for each language
## c.!!) for German, calculate score for each annotator + average
## - without parameters:
## d) crosslingual Smatch score for empty structures

smatch_scores = {}

# Collect all filepath names:

AMR_filepaths = {
    'empty': {},
    'annotated': {}
}

blocks = list(range(number_of_blocks))
block_names = []
for block_number in blocks:
    block_names.append(f'de-block{str(block_number).zfill(3)}')

for language in languages:
    AMR_filepaths['empty'][language] = []
    for block_name in block_names:
        current_filepath = f'{files_for_score_dir}/smatch_format_{language}_{block_name}.txt'
        AMR_filepaths['empty'][language].append(current_filepath)

for annotation_abbreviation in annotation_abbreviations:
    AMR_filepaths['annotated'][annotation_abbreviation] = {}
    for param_combination in param_combinations:
        param_name = f'params{param_combination}'
        AMR_filepaths['annotated'][annotation_abbreviation][param_name] = []
        for block_name in block_names:
            current_filepath = f"{files_for_score_dir}/smatch_format_{annotation_abbreviation}_{param_name}_{block_name}.txt"
            AMR_filepaths['annotated'][annotation_abbreviation][param_name].append(current_filepath)

lt_sr = ['lt','sr']
lt_sr_filepaths = [[],[]]
de_lt_sr_filepaths = {}
interannotator_filepaths = {}
empty_vs_annotated_filepaths = {}
empty_filepaths = {}

for language in lt_sr:
    de_lt_sr_filepaths[language] = {}
    for annotator in annotators:
        de_lt_sr_filepaths[language][annotator] = [[],[]]


for param_combination in param_combinations:
    param_name = f'params{param_combination}'

    # lt-sr
    lt_sr_filepaths[0] = AMR_filepaths['annotated']['lt'][param_name]
    lt_sr_filepaths[1] = AMR_filepaths['annotated']['sr'][param_name]
    smatch_scores[f'crosslingual_lt-sr-{param_combination}'] = calculate_scores(lt_sr_filepaths)

    # de-lt and de-sr:
    block_scores_de = {}
    for language in lt_sr:
        block_scores_de[language] = {}
        block_scores_de[language] = {}
        for annotator in annotators: 
            # mind that all scores all calculated here, also for those files not annotated
            de_lt_sr_filepaths[language][annotator][0] = AMR_filepaths['annotated'][f'de_{annotator}'][param_name]
            de_lt_sr_filepaths[language][annotator][1] = AMR_filepaths['annotated'][language][param_name]
            scores = calculate_scores(de_lt_sr_filepaths[language][annotator])
            smatch_scores[f'crosslingual_de_{annotator}-{language}-{param_combination}'] = scores
            # add corrected average based on annotated files only:
            corrected_average = round(statistics.mean([score[1] for score in enumerate(scores[0]) if score[0] in annotated_german_files_dict[annotator]]),2)
            smatch_scores[f'crosslingual_de_{annotator}-{language}-{param_combination}'] = [scores[0],scores[1],corrected_average]

        # calculate average score for each file based on actually annotated files per annotator
        smatch_scores[f'crosslingual_de-{language}-{param_combination}'] = [[],[]]
        for block_number in blocks:
            block_scores_de[language][block_number] = []
            for annotator in annotators:
                if block_number in annotated_german_files_dict[annotator]:
                    block_scores_de[language][block_number].append(smatch_scores[f'crosslingual_de_{annotator}-{language}-{param_combination}'][0][block_number])
            average_block_score = round(statistics.mean(block_scores_de[language][block_number]),2)
            smatch_scores[f'crosslingual_de-{language}-{param_combination}'][0].append(average_block_score)
        smatch_scores[f'crosslingual_de-{language}-{param_combination}'][1] = round(statistics.mean(smatch_scores[f'crosslingual_de-{language}-{param_combination}'][0]),2)


    # interannotator (ann1-ann2, ann1-ann3, ann2-ann3):
    annotation_pairs = [('ann1','ann2'),('ann1','ann3'),('ann2','ann3')]
    for annotatorA, annotatorB in annotation_pairs:
        interannotator_filepaths[f'{annotatorA}-{annotatorB}'] = [[],[]]
        for block_number in blocks:
            if (block_number in annotated_german_files_dict[annotatorA]) and (block_number in annotated_german_files_dict[annotatorB]):
                interannotator_filepaths[f'{annotatorA}-{annotatorB}'][0].append(AMR_filepaths['annotated'][f'de_{annotatorA}'][param_name][block_number])
                interannotator_filepaths[f'{annotatorA}-{annotatorB}'][1].append(AMR_filepaths['annotated'][f'de_{annotatorB}'][param_name][block_number])
        smatch_scores[f'interannotator_de_{annotatorA}-de_{annotatorB}-{param_combination}'] = calculate_scores(interannotator_filepaths[f'{annotatorA}-{annotatorB}'])

    ## empty vs annotated: de (ann1, ann2, ann3):
    empty_vs_annotated_filepaths['de'] = {}
    block_scores_de['empty'] = {}
    for annotator in annotators: 
        # mind that all scores all calculated here, also for those files not annotated
        empty_vs_annotated_filepaths['de'][annotator] = [[],[]]
        empty_vs_annotated_filepaths['de'][annotator][0] = AMR_filepaths['annotated'][f'de_{annotator}'][param_name]
        empty_vs_annotated_filepaths['de'][annotator][1] = AMR_filepaths['empty']['de']
        scores = calculate_scores(empty_vs_annotated_filepaths['de'][annotator])
        smatch_scores[f'empty_vs_annotated_de_{annotator}-{param_combination}'] = scores
        # add corrected average based on annotated files only:
        corrected_average = round(statistics.mean([score[1] for score in enumerate(scores[0]) if score[0] in annotated_german_files_dict[annotator]]),2)
        smatch_scores[f'empty_vs_annotated_de_{annotator}-{param_combination}'] = [scores[0],scores[1],corrected_average]

    # calculate average score for each file based on actually annotated files per annotator
    smatch_scores[f'empty_vs_annotated_de-{param_combination}'] = [[],[]]
    for block_number in blocks:
        block_scores_de['empty'][block_number] = []
        for annotator in annotators:
            if block_number in annotated_german_files_dict[annotator]:
                block_scores_de['empty'][block_number].append(smatch_scores[f'empty_vs_annotated_de_{annotator}-{param_combination}'][0][block_number])
        average_block_score = round(statistics.mean(block_scores_de['empty'][block_number]),2)
        smatch_scores[f'empty_vs_annotated_de-{param_combination}'][0].append(average_block_score)
    smatch_scores[f'empty_vs_annotated_de-{param_combination}'][1] = round(statistics.mean(smatch_scores[f'empty_vs_annotated_de-{param_combination}'][0]),2)


    ## empty vs annotated: lt, sr
    for language in lt_sr:
        empty_vs_annotated_filepaths[language] = [[],[]]
        empty_vs_annotated_filepaths[language][0] = AMR_filepaths['annotated'][language][param_name]
        empty_vs_annotated_filepaths[language][1] = AMR_filepaths['empty'][language]
        smatch_scores[f'empty_vs_annotated_{language}-{param_combination}'] = calculate_scores(empty_vs_annotated_filepaths[language])

# empty structures (de-lt, de-sr, lt-sr):
for language in languages:
    empty_filepaths[language] = AMR_filepaths['empty'][language]
language_pairs = [('de','lt'),('de','sr'),('lt','sr')]
for languageA, languageB in language_pairs:
    smatch_scores[f'empty_{languageA}-{languageB}'] = calculate_scores([empty_filepaths[languageA],empty_filepaths[languageB]])


# save all scores into output file:
for score_heading in smatch_scores:
    with open(output_filepath_for_scores, 'a') as output_file:
        output_file.write(f'{score_heading}: {smatch_scores[score_heading]}\n')
with open(output_filepath_for_scores, 'a') as output_file:
            output_file.write(f'############## data analysis completed ###############\n')