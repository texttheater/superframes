import sys
import ast

def convert_files_to_dict(annotations, sentence_alignment):
    """
    Converts annotated or empty SF-files (in form of a dict of strings) into a nested dict.
    If additionaly a file with the sentence alignment is provided, only those sentences that appear in the alignment mapping are kept.

    Args:
        annotations (dict):
            dictionary containing SF structures as string
        sentence_alignment (dict or None):
            all annotations keys must agree in first characters with a sentence_alignment key

    Returns:
        dict: a nested dictionary containing frame and role annotations, optionally filtered by sentence alignment
    """
    next_edge_is_frame = True
    dict_frames_roles_word_ids = {}
    for annotation in annotations:
        dict_frames_roles_word_ids[annotation] = {}
        for line in annotations[annotation].splitlines(keepends=True):
            if line.startswith(f'# sent_id = '):
                sent_id = int(line[12:-1])
                dict_frames_roles_word_ids[annotation][sent_id] = {}
                next_edge_is_frame = True
                frame = ''
                role = ''
                continue  
            if line == '\n':
                next_edge_is_frame = True
                role = ''
                continue
            # extracting role labels:
            if not next_edge_is_frame and line.startswith('['):
                role = line.split(']', 1)[0] + ']'
                try:
                    word_id_role = int(line.split('(', 1)[1].split(')', 1)[0])
                except:
                    word_id_role = int(line.split('(')[2].split(')', 1)[0])
                dict_frames_roles_word_ids[annotation][sent_id][word_id_frame]["roles"].update({word_id_role: role})
            # extracting frame labels:
            if next_edge_is_frame and line.startswith('['):
                frame = line.split(']', 1)[0] + ']'
                try:
                    word_id_frame = int(line.split('(', 1)[1].split(')', 1)[0])
                except:
                    word_id_frame = int(line.split('(')[2].split(')', 1)[0])
                next_edge_is_frame = False
                word = line.split(']', 1)[1].split('(', 1)[0].strip()
                dict_frames_roles_word_ids[annotation][sent_id].update({word_id_frame: {"frame_label": frame, "word": word, "roles": {}}})
                continue
            # sentence done

    if sentence_alignment: # remove all unaligned sentences
        aligned_dict_frames_roles_word_ids = {}
        for annotation in annotations:
            aligned_dict_frames_roles_word_ids[annotation] = {}
            for aligned_sent_id in sentence_alignment[annotation[:2]]:
                aligned_dict_frames_roles_word_ids[annotation][aligned_sent_id] = dict_frames_roles_word_ids[annotation][aligned_sent_id]
        return aligned_dict_frames_roles_word_ids

    return dict_frames_roles_word_ids


if __name__ == "__main__":
    output_filepath = sys.argv[1]
    input_sentence_alignment_filepath = sys.argv[2] # file path with sentence alignments. if "file" not found, unaligned annotation files are assumed
    input_annotation_filepaths = sys.argv[3:] # file paths for annotation files
    

    annotations = {}
    for annotation_filepath in input_annotation_filepaths:
        annotation_filename = annotation_filepath.split("/")[-1].split(".")[0]
        with open(annotation_filepath, 'r') as annotation_file:
            annotation = ''
            for line in annotation_file:
                annotation += line
            annotations[annotation_filename] = annotation

    try:
        with open(input_sentence_alignment_filepath, 'r') as f:
            sentence_alignment = f.read()
            print("Sentence alignment argument passed. If this is not intended, change second argument to '-' or similar.")
            sentence_alignment = ast.literal_eval(sentence_alignment)
    except:
        sentence_alignment = None

    with open(output_filepath, 'w') as f:
        print(convert_files_to_dict(annotations, sentence_alignment),file=f)

