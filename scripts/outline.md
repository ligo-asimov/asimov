Free-form text can go here. You can write information about this event in standard markdown here and the bot will ignore it.

In the run information block please use YAML markup to specify the metadata and production information for this event. See the [README](https://git.ligo.org/pe/O3/o3b-pe-coordination) on this repository for more information on the format this should take.

# Event information and links

+ [Event PE repository](https://git.ligo.org/pe/O3/{{ event_object.meta['old superevent'] }})


# Run information
```yaml
---
{{ yaml}}
---
```


	  

/label ~trigger ~"trigger-o3b"
/epic &1
/milestone %1
