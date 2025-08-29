import ast
import sys
import math

def create_smatch_formatted_annotations(annotation_dict_for_analysis,parameters=[0,0,0,0]):
    '''
    Turns annotation dictionary into AMR / Smatch readable format such that Smatch score can be calculated from the output.

    Args:
        annotation_dict_for_analysis (dict): Superframes annotations as python dictionary
        parameters (list/str): 4 parameters (1 or 0 each) whether to drop (1) aspect, polarity, mode or neutralize argument prefix or not (0). Can be a string '0000' or a list [0,0,0,0]

    Returns:
        str: AMR / Smatch readable format of input annotations
    '''
    smatch_formatted_annotations = {}
    for language_annotation in annotation_dict_for_analysis:
        smatch_formatted_annotations[language_annotation] = {}
        for sent_id in annotation_dict_for_analysis[language_annotation]:
            smatch_formatted_annotations[language_annotation][sent_id] = ''
            seen_word_ids = []
            smatch_formatted_annotations[language_annotation][sent_id] += f"\n# {language_annotation}, sent_id = {sent_id}\n"
            annotation_frame = annotation_dict_for_analysis[language_annotation][sent_id]
            smatch_formatted_annotations[language_annotation][sent_id] +="(0 / root"
            for word_id in annotation_frame:
                word_id = int(word_id)
                if word_id not in seen_word_ids:
                    smatch_formatted_annotations[language_annotation][sent_id] += "\n      :predicate"
                    smatch_format = extract_roles(annotation_dict_for_analysis[language_annotation][sent_id],word_id, 2, seen_word_ids, parameters)
                    smatch_formatted_annotations[language_annotation][sent_id] += smatch_format
            smatch_formatted_annotations[language_annotation][sent_id] += ")\n"
    return smatch_formatted_annotations

def extract_roles(sent_id_dict, word_id, ebene, seen_word_ids, parameters, edge_for_mscene = None):
    '''
    Auxiliary method of create_smatch_formatted_annotations to extract all Superframes roles of a word in a sentence and convert them into AMR / Smatch readable format.

    Args:
        sent_id_dict (dict): subpart of annotation dict for sentence of the word to be examined
        word_id (int): word_id of word to be examined
        ebene (int): the current amount of indendation for the next line in the final output
        seen_word_ids (list(int)): list of word_ids for words that do not need to be examined further
        parameters (list/str): 4 parameters whether to drop aspect, polarity, mode or neutralize argument prefix
        edge_for_mscene (str or None): indicates whether and if yes, which additional edge is needed to achieve equivalence for m-scene structures
    
    Returns:
        str: AMR / Smatch readable substring including all roles for the given word_id
    '''
    _,_,_, neutralize_argument_prefix = [int(p) for p in parameters]
    roles = sent_id_dict[word_id]["roles"]
    frame_annotation = sent_id_dict[word_id]["frame_label"]
    frames = split_annotations(frame_annotation, parameters)
    indentation = "      " * ebene
    if word_id in seen_word_ids:
        return f" {word_id}"
    smatch_format = f"({word_id} / frame"
    for frame in frames:
        smatch_format += f'\n{indentation}:frame "{frame}"'
    seen_word_ids.append(word_id)
    if edge_for_mscene:
        smatch_format += f'\n{indentation}{edge_for_mscene}'
    if roles == {}:
        return smatch_format + ")"
    else:
        ebene += 1
        for role_word_id in roles:
            role = roles[role_word_id]
            alternative_role_labels = split_annotations(role, parameters)
            for alternative_role_label in alternative_role_labels:
                if is_equivalent_to_scene(sent_id_dict, alternative_role_label, role_word_id):
                    if neutralize_argument_prefix:
                        smatch_format += f"\n{indentation}:n-scene"
                    else:
                        smatch_format += f"\n{indentation}:m-scene"
                    edge_for_mscene = f":{is_equivalent_to_scene(sent_id_dict, alternative_role_label, role_word_id)} {word_id}"
                else:
                    smatch_format += f"\n{indentation}:{alternative_role_label}"
                    edge_for_mscene = None
                try:
                    smatch_format += extract_roles(sent_id_dict, role_word_id, ebene, seen_word_ids, parameters, edge_for_mscene)
                except:
                    smatch_format += f" {role_word_id}"
        smatch_format += ")"
    return smatch_format

def split_annotations(annotation, parameters):
    '''
    Turns annotation for one frame or role into list of labels and modifies each label according to parameters given.

    Args:
        annotation (str): SF-annotation for one word_id (frame or role)
        parameters (list/str): 4 parameters whether to drop aspect, polarity, mode or neutralize argument prefix

    Returns:
        list: list of alternative labels which are modified according to parameters. Contains 1 element if there are no alternatives. This element is "-" if role or frame was not annotated.
    '''
    if annotation == "[]":
        return ["-"]
    annotation_list_inter1 = annotation.strip("[]").split(" || ")
    labels = []
    for item in annotation_list_inter1:
        annotation_list_inter2 = item.split(" >> ")
        labels.extend(annotation_list_inter2)
    for i in range(len(labels)):
        labels[i] = drop_or_neutralize_affix(labels[i], parameters)
    return labels

def drop_or_neutralize_affix(label, parameters):
    '''
    Modifies Superframes label such that aspect, polarity, mode are dropped and/or argument prefix neutralized.

    Args:
        label (str): Superframes label
        parameters (list/str): 4 parameters (1 or 0 each) whether to drop (1) aspect, polarity, mode or neutralize argument prefix or not (0). Can be a string '0000' or a list [0,0,0,0]
    
    Returns:
        str: modified label according to parameters given
    '''
    drop_aspect, drop_polarity, drop_mode, neutralize_argument_prefix = [int(p) for p in parameters]
    aspect_affixes = ["target-", "initial-", "transitory-", "-INIT", "-CHANGE", "-DEINIT", "-CONTINUATION", "-PREVENTION"] # previous Superframes guideline contains -PREVENTION suffix
    modified_label = label
    if drop_aspect:
        for affix in aspect_affixes:
            modified_label = modified_label.replace(affix, "")
    if drop_polarity:
        modified_label = modified_label.replace("-NEG", "")
    if drop_mode:
        modified_label = modified_label.replace("-NECESSITY","").replace("-POSSIBILITY", "")
    if neutralize_argument_prefix and (modified_label.startswith("m-") or modified_label.startswith("x-")):
        modified_label = "n" + modified_label[1:] # "n" for "neutralized"
    return modified_label
    
def is_equivalent_to_scene(sent_id_dict, role_label, role_word_id):
    '''
    Checks whether a given role label is equivalent to m-scene according to Superframes manual (section "Modifiers") 

    Args:
        sent_id_dict (dict): subpart of annotation dict for sentence of the word to be examined
        role_label (str): one Superframes role label for word to be examined
        role_word_id (int): word_id of word to be examined
    
    Returns:
        str or None: label that needs to be added according to manual. None in case the input label does not qualify for equivalence to m-scene
    '''
    irregular_equivalences = {"event": "undergoer", "activity": "is-active", "explanation": "explained", "means": "purpose"} # ARG1 = has-ARG2 not applicable
    exceptions = ["scene", "hitting", "reaction", "subclass"] # label is "m-scene" or ARG1 instead of ARG2 has the same label as the frame
    try:
        frame_annotation = sent_id_dict[role_word_id]["frame_label"]
        if role_label[1] != "-":
            return None # label is not modifier role
    except:
        return None
    frames = split_annotations(frame_annotation, [1,1,1,1]) # remove or neutralize all affixes
    if role_label[2:] in exceptions:
        return None
    if role_label[2:].upper() in frames:
        if role_label[2:] in irregular_equivalences:
            return irregular_equivalences[role_label[2:]]
        else:
            return f'has-{role_label[2:]}'
    else:
        return None
    
def organize_in_blocks(smatch_formatted_annotations,sentence_alignment, leading_language, number_of_blocks, block_size, output_dir = None, keyword = ''):
    '''
    Reorganizes the given input into blocks.

    Args:
        smatch_formatted_annotations (dict): input dictionary for annotations in AMR / Smatch readable format
        sentence_alignment (dict): dictionary where all aligned sentence_ids per language (key) are listed
        leading_language (str): key in sentence_alignment according to whose sentence_ids the blocks are to be organized
        number_of_blocks (int): number of blocks (or files to be saved)
        block_size (int): block size in terms of sentence ids (e.g. sentence_ids 1-50, 51-100, ...)
        output_dir (str or None): output directory to save each blocks in a seperate file. If None, files are not saved.
        keyword (str): keyword to tag the output filenames. Empty string per default.

    Returns:
        dict: dictionary where input is organized in blocks
    '''
    annotations_in_blocks = {}
    aligned_sentences_leading_annotation = sentence_alignment[leading_language]
    for annotation in smatch_formatted_annotations:
        annotations_in_blocks[annotation] = {}
        for block_number in range(number_of_blocks):
            block_name = f'block{str(block_number).zfill(3)}'
            annotations_in_blocks[annotation][block_name] = []
        aligned_sentences_current_annotation = sentence_alignment[annotation[:2]]
        for n, sent_id_current_annotation in enumerate(aligned_sentences_current_annotation):
            sent_id_leading_annotation = aligned_sentences_leading_annotation[n]
            block = math.floor((sent_id_leading_annotation-1)/block_size)
            annotations_in_blocks[annotation][f'block{str(block).zfill(3)}'].append(smatch_formatted_annotations[annotation][sent_id_current_annotation])
    
    if output_dir:
        if keyword != '':
            keyword = f'_{keyword}'
        for annotation in annotations_in_blocks:
            blocks = annotations_in_blocks[annotation]
            for block_name in blocks:
                output_filepath = f'{output_dir}/smatch_format_{annotation}{keyword}_{leading_language}-{block_name}.txt'
                with open(output_filepath, "w") as output_file:
                    for sent in blocks[block_name]:
                        output_file.write(sent)
    
    return annotations_in_blocks

if __name__ == "__main__":
    input_dict_filepath = sys.argv[1]
    output_dir = sys.argv[2]
    drop_aspect = int(sys.argv[3])
    drop_polarity = int(sys.argv[4])
    drop_mode = int(sys.argv[5])
    neutralize_argument_prefix = int(sys.argv[6])
    
    parameters = [drop_aspect,drop_polarity,drop_mode,neutralize_argument_prefix]

    with open(input_dict_filepath) as input_dict_file:
        dict_str = input_dict_file.read()
        annotation_dict_for_analysis = ast.literal_eval(dict_str)

    params = f"params{drop_aspect}{drop_polarity}{drop_mode}{neutralize_argument_prefix}"

    smatch_formatted_annotations = create_smatch_formatted_annotations(annotation_dict_for_analysis,parameters)

    if len(sys.argv) > 7:
        leading_language = sys.argv[7] # e.g. 'de'
        number_of_blocks = int(sys.argv[8]) # e.g. '11'
        block_size = int(sys.argv[9]) # e.g. '50    
        input_sentence_alignment_filepath = sys.argv[10]
        with open(input_sentence_alignment_filepath) as input_sentence_alignment_file:
            dict_sent_alignment = input_sentence_alignment_file.read()
            sentence_alignment = ast.literal_eval(dict_sent_alignment)

        annotations_in_blocks = organize_in_blocks(smatch_formatted_annotations,sentence_alignment, leading_language, number_of_blocks, block_size, output_dir, f'params{params}')

    else:
        for annotation in smatch_formatted_annotations:
            with open(f"{output_dir}/smatch_format_{annotation}_{params}.txt", "w") as output_file:
                for sent_id in smatch_formatted_annotations[annotation]:
                    output_file.write(smatch_formatted_annotations[annotation][sent_id])

    
    
   
