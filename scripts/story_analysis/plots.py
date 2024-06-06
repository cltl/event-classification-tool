import matplotlib.pyplot as plt
import numpy as np


colors = {"S": "#f3a6c5", "E": "#abebc6", "C": "#9cadce"}
color_palette = ['#f3a6c5','#abebc6','#9cadce']

def plot_tag_distribution(dist_df,filename,unit="Chapter",chapter_boundaries=None):

    tags = list(dist_df.keys())

    categories = range(1, len(dist_df[tags[0]]) + 1)


    plt.figure(figsize=(7, 6))

    for ind,tag in enumerate(tags):
        plt.plot(categories, dist_df[tag], label=tag, color=color_palette[ind])


    # If chapter_boundaries is provided, draw vertical lines at these x-coordinates
    if chapter_boundaries is not None:
        for boundary in chapter_boundaries:
            plt.axvline(x=boundary, color='lightgrey', linestyle='--',alpha=0.5) 
    
    plt.xlim(0, len(categories)+1)

    plt.xlabel(unit)
    plt.ylabel('Relative frequency')
    plt.legend()
    plt.savefig(filename)
    plt.clf()


def plot_entropy(entropy_dict, filename,nchunks=None,chapter_boundaries=None):

    categories = list(entropy_dict.keys())
    entropy_values = np.array(list(entropy_dict.values()))

    plt.figure(figsize=(12, 6))
    
    plt.plot(range(len(categories)), entropy_values, color='black')

    if chapter_boundaries is not None:
        for boundary in chapter_boundaries:
            plt.axvline(x=boundary, color='lightgrey', linestyle='--',alpha=0.5) 

    if "smooth.pdf" in filename:
        # Display every 20th chunk number, starting from 1
        tick_positions = range(0, len(categories), 20)
        tick_labels = range(0, len(categories)+1, 20)
        plt.xticks(tick_positions, tick_labels, rotation=90)
    else:
        plt.xticks(range(len(categories)), categories, rotation=90)

    if nchunks:
        xlabel = "{nchunks} Chunks in Book"
    else:
        xlabel = "Book Chapters"

    plt.ylabel('Entropy')
    plt.xlabel(f"{xlabel}")
    plt.tight_layout()
    plt.savefig(filename)
    plt.clf()



def plot_moving_averages(mydict, spans, current_chapter, output_dir):
    plt.figure(figsize=(7, 6))


    # Reset plot parameters
    plt.rcParams.update(plt.rcParamsDefault)

    ax = plt.gca()

    for tag, averages in mydict.items():
        plt.plot(spans, averages, label=f'Tag{tag}', color=colors[tag])

    plt.xlabel('#Texts')
    plt.ylabel('Average')


    for spine in ax.spines.values():
        spine.set_linewidth(1.1)

    plt.xlim([min(spans)-0.5, max(spans)])
    plt.savefig(f"{output_dir}/chapter_{current_chapter}.pdf")


def barplot_tags(data,saving_file):

    keys = list(data.keys())
    values = list(data.values())
    bar_colors = [colors[key] for key in keys]

    plt.figure(figsize=(8, 6))
    plt.bar(keys, values, color=bar_colors)


    plt.xlabel('Labels')
    plt.ylabel('#Annotated Texts')

    plt.tight_layout()
    plt.savefig(saving_file)
    plt.clf()