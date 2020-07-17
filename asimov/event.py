"""
Trigger handling code.
"""

import yaml

class DescriptionException(Exception):
    def __init__(self, message, issue, production):
        super(DescriptionException, self).__init__(message)
        self.message = message
        self.issue = issue
        self.production = production

    def __repr__(self):
        text = f"""
An error was detected with the YAML markup in this issue.
Please fix the error and then remove the `yaml-error` label from this issue.
<p>
  <details>
     <summary>Click for details of the error</summary>
     <p><b>Production</b>: {self.production}</p>
     <p>{self.message}</p>
  </details>
</p>

- [ ] Resolved
"""
        return text

    def submit_comment(self):
        if self.issue:
            self.issue.add_label("yaml-error", state=False)
            self.issue.add_note(self.__repr__())
    
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
        event.issue_object = issue
        for production in data['productions']:
            try:
                event.add_production(Production.from_dict(production, event=event, issue=issue))
            except DescriptionException as e:
                e.submit_comment()
        
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
    def from_dict(cls, parameters, event, issue=None):
        name, pars = list(parameters.items())[0]
        # Check all of the required parameters are included
        if not {"status", "pipeline"} <= pars.keys():
            raise DescriptionException(f"Some of the required parameters are missing from {name}", issue, name)
        if not "comment" in pars:
            pars['comment'] = None
        return cls(event, name, pars['status'], pars['pipeline'], pars['comment'])
    
    def __repr__(self):
        return f"<Production {self.name} for {self.event} | status: {self.status}>"
