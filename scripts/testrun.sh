codename=rift
rm -rf new-project-$codename

mkdir new-project-$codename
cd new-project-$codename
asimov init "new project $codename"

asimov apply -f https://git.ligo.org/asimov/data/-/raw/6-add-the-state-vector-to-the-analysis-defaults-files/defaults/testing-pe.yaml
asimov apply -f https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe-priors.yaml

asimov apply -f https://git.ligo.org/asimov/data/-/raw/main/events/gwtc-2-1/GW150914_095045.yaml
#asimov apply -f https://git.ligo.org/asimov/data/-/raw/main/analyses/production-default.yaml -e GW150914_095045

asimov apply -f ../../tests/test_data/test_rift.yaml 

asimov manage build
asimov manage submit --dryrun
