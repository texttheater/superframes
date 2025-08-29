import subprocess
import sys
import statistics

def calculate_scores(annotation_filepaths):
    """
    Runs the external smatch.py script on pairs of annotation files to compute similarity scores

    Args: 
        annotation_filepaths (list):
            a list of two lists containing file paths for each member in the pair respectively

    Returns:
        tuple (list,float):
            list: a list of smatch scores, one for each annotation pair
            float: the average smatch score, rounded by 2 decimals
    """
    scores = []
    for filepath1, filepath2 in zip(annotation_filepaths[0],annotation_filepaths[1]):
        result = subprocess.run(
            ["smatch.py", "-f", filepath1, filepath2],
            capture_output=True, 
            text=True
        )
        scores.append(float(result.stdout[-5:-1]))
    average_score = round(statistics.mean(scores),2)
    return scores, average_score


if __name__ == "__main__":
    """
    Usage:
        python3 score_calculation.py <keyword_for_output> <number_of_blocks> <filepath_A> <filepath_B> <file_ending> <output_filepath> [leave_out_blocks]
    """
    heading = sys.argv[1] # e.g. "LT-SR-params0000"
    number_of_blocks = int(sys.argv[2]) # e.g. 11
    filepath_annotation_A = sys.argv[3]
    filepath_annotation_B = sys.argv[4]
    file_ending = sys.argv[5]
    output_filepath = sys.argv[6]

    try:
        leave_out_blocks = [int(item) for item in sys.argv[7].split("-")]
    except:
        leave_out_blocks = None

    annotation_filepaths = [[],[]]

    if number_of_blocks == 1:
        annotation_filepaths[0].append(filepath_annotation_A)
        annotation_filepaths[1].append(filepath_annotation_B)
    elif number_of_blocks > 1:
        blocks = list(range(number_of_blocks))
        if leave_out_blocks:
            blocks = list(set(blocks) - set(leave_out_blocks))
        for block_number in blocks:
            annotation_filepaths[0].append(f"{filepath_annotation_A}{str(block_number).zfill(len(str(number_of_blocks)))}.{file_ending}")
            annotation_filepaths[1].append(f"{filepath_annotation_B}{str(block_number).zfill(len(str(number_of_blocks)))}.{file_ending}")

    scores = calculate_scores(annotation_filepaths)

    with open(output_filepath, 'a') as output_file:
        output_file.write(f"{heading}: {scores}\n")
    
    print(f"{heading}: {scores}")