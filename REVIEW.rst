0.3.0
=====

(25.4.2021) We have performed line-by-line reviews of the core functions of asimov, the PE automation pipeline for O3a final. The review covered the generation of the workflow, DAGs and command lines for BayesWave, bilby (via bilby_pipe) and RIFT. The handling of LALInference was not reviewed here.
The reviewed code packages and files are listed in the table below. All requested fixes were implemented on the review branch and are signed off, ready to be merged upstream into master (!5). Several new logger messages were added. All requests and fixes are documented in the relevant issues and MRs. Significant changes affect the

BayesWave settings for PSD generation
PE summary generation for results generation
Passing of a bilby prior file directly via the ini file instead of the CL
Removal of the ROQ priors as default
Passing of the minimum template frequency for RIFT

A new set of integration tests was added but we note that these do not allow for a complete end-to-end test of the asimov pipeline as the interfacing with gitlab was removed (on purpose); hence the git issue generation and gitlab interactions are not covered in these tests. They serve the purpose of demonstrating the correct generation of ini files and DAGs/CLs.
A complete end-to-end test with all fixes implemented on the review branch was performed on a test-trigger event (copy of GW190426l) with the BayesWave dependencies removed: pe/O3/o3b-pe-coordination#122 with the generated ini files ProdF{6,7,8} available at https://git.ligo.org/daniel-williams/S190426l/-/tree/master/C01_offline
The correct end-to-end workflow was produced.
The MR !5 will be merged upstream, with the reviewed version of asimov corresponding to version v0.3.0. This version of asimov should be used for all O3 production analysis.
In addition, we have also reviewed and signed off on default inputs specific to the O3a final analysis. While many of these defaults are also applicable to the O3b analysis, e.g. default calibration C01_offline, channel names etc., we recommend a thorough re-check of these settings specific for O3b.
For the future, we recommend further improvement in logging messages, the writing of a documentation and a workflow-chart. We also note that the spin magnitude priors are currently hard-coded for RIFT. Hence, we recommend implementing the BBH magnitudes as the default option but allowing for these to be populated via the prior metadata. Extensions to consistently handling BNS and NSBH as well as allowing for other schedulers will likely be required in the future.
