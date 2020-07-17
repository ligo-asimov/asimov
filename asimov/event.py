"""
Trigger handling code.
"""

import yaml

class Event:
    """
    A specific gravitational wave event or trigger.
    """
    
    def __init__(self, name, repository, **kwargs):
        self.name = name
        self.repository = repository
        self.productions = []
        self.meta = kwargs
    
    def add_production(self, production):
        """
        Add an additional production to this event.
        """
        self.productions.append(production)
    
    def __repr__(self):
        return f"<Event {self.name}>"
    
    @classmethod
    def from_issue(cls, issue):
        """
        Parse an issue description to generate this event.
        """
        
        text = issue.text.split("---")
        
        data = yaml.load(text[1])
        
        event = cls(data['name'], data['repository'])
        event.text = text
        for production in data['productions']:
            try:
                event.add_production(Production.from_dict(production, event=event))
            except KeyError:
                pass
        
        return event
    
    def to_yaml(self):
        """Serialise this object as yaml"""
        data = {}
        data['name'] = self.name
        data['repository'] = self.repository
        for key, value in self.meta.items():
            data[key] = value
        data['productions'] = []
        for production in self.productions:
            data['productions'].append(production.to_dict())
            
        return yaml.dump(data)
    
    def to_issue(self):
        self.text[1] = "\n"+self.to_yaml()
        return "---".join(self.text)

class Production:
    """
    A specific production run.
    
    Parameters
    ----------
    event : `asimov.event`
        The event this production is running on.
    name : str
        The name of this production.
    status : str
        The status of this production.
    pipeline : str
        This production's pipeline.
    comment : str
        A comment on this production.
    """
    def __init__(self, event, name, status, pipeline, comment=None):
        self.event = event
        self.name = name
        self.status = status.lower()
        self.pipeline = pipeline.lower()
        self.comment = comment

    def to_dict(self):
        output = {self.name: {}}
        output[self.name]['status'] = self.status.lower()
        output[self.name]['pipeline'] = self.pipeline.lower()
        output[self.name]['comment'] = self.comment
        return output
        
    @classmethod
    def from_dict(cls, parameters, event):
        name, pars = list(parameters.items())[0]
        # Check all of the required parameters are included
        if not {"status", "pipeline"} <= pars.keys():
            raise KeyError
        if not "comment" in pars:
            pars['comment'] = None
        return cls(event, name, pars['status'], pars['pipeline'], pars['comment'])
    
    def __repr__(self):
        return f"<Production {self.name} for {self.event} | status: {self.status}>"
