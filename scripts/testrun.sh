rm -rf new-project

mkdir new-project
cd new-project
asimov init "new project"

asimov apply -f https://git.ligo.org/asimov/data/-/raw/main/defaults/testing-pe.yaml
asimov apply -f https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe-priors.yaml

asimov apply -f https://git.ligo.org/asimov/data/-/raw/main/events/gwtc-2-1/GW150914_095045.yaml
asimov apply -f https://git.ligo.org/asimov/data/-/raw/main/analyses/production-default.yaml -e GW150914_095045

#asimov manage build
#asimov manage submit
