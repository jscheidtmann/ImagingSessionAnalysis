# Data Driven Astro Imaging

Is your guiding good? What is the seeing? Is the mount working properly? How bad is the seeing? 

Which of the latest changes I did have had a positive influence on my sub-exposures?

All these are questions that are top of mind for an astrophotographer. A lot of tweaking and „optimization“ will be done on perceived imperfections of the setup. But what is really a necessary optimization? Which of them did have a positive effect? And when did you reach the point of diminishing returns?

D-DAI is going to answer some of these questions and help master the learning curve of deep sky imaging, by applying a data-driven, measurable approach: 

The idea is to use objective measures of image quality, such as HFR, FWHM and similar and relate these to other parameters and statistics that are measured during image acquisition, be it weather, guiding information, focus runs and any other information. 

By first applying simple rules, providing simple suggestions to optimise your astro-imaging, D-DAI‘s vision is to become more and more sophisticated, provide better and better recommendations over time until sophisticated, trained models help you achieve „perfect“ results. 

The goal is to make the tacit knowledge of the best astrophotographers explicit in a community effort, so that it becomes available to everyone, willing to invest the effort of optimising his or her Astro-imaging.

# Imaging Session Analysis  

„Okay“, you say, „what does the software really do?“

At first D-DAI will make all data that is collected during an imaging session available for an exploratory analysis, i.e. for visualisations.
 
You can import information stored in:

 * fits-headers of your sub-exposures
 * ImageMetaData.csv & AcquisitionDetails.csv generated by the N.I.N.A. Session Metadata plugin
 * the PHD2 Guidelog
  
This software is based on code developed by Jürgen Terpe and the GraXpert team.

## Installation 

### Windows

Download the zip-package from the Release page, unzip it into a directory on your harddisk and double-clock on `ImagingSessionAnalysis.exe`

### Mac

Download the dmg-package from the Release page and install it. This is unsigned, so you will have to do some extra clicks, so that you‘re finally allowed to install it.

### Linux

At the moment there‘s no Linux packaged version available, but the code should run on recent desktop versions. `git clone` it into a directory of your choosing, cd into `src` and run `python3 ImagingSessionAnalysis.py`.
