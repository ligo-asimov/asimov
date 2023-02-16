Contributing to asimov
======================

Asimov is designed to make working with parameter estimation pipelines easier.
This is often a complicated job, which requires familiarity with both computing infrastructure and individual pipelines, so we're always keen to receive help from anyone who is willing to lend a hand, be that via a bug fix, an issue report, or implementing an interface to a new pipeline.

This is a short guide to contributing to asimov, which is aimed at anyone who has a little familiarity with python and git.  

Code of Conduct
---------------

Everyone participating in the asimov project, and in particular in our issue tracker, merge requests, and chat channels, is expected to treat other people with respect.
Please familiarise yourself with our full code of conduct, which is based on the contributor covenant, and available in the CODE-OF-CONDUCT.rst file in this repository.

Code style
----------

During a code review (when you want to contribute changes to the code base), you may be asked to change your code to fit with the asimov style.
This is based on a few python conventions and is generally maintained to ensure the code base remains consistent and readable to new users.
Here we list some typical things to keep in mind ensuring the code review is as smooth as possible

1. We follow the `standard python PEP8 <https://www.python.org/dev/peps/pep-0008/>`_ conventions for style. While the testing of this is largely automated (the C.I. pipeline tests check using `flake8 <http://flake8.pycqa.org/en/latest/>`_), some more subjective things might slip the net. 
2. New classes/functions/methods should have a docstring and following the `numpy docstring guide  <https://numpydoc.readthedocs.io/en/latest/format.html>`_, for example

.. code-block:: python
		
      def my_new_function(x, y, print=False):
	  """
	  A function to calculate the sum of two numbers

	  Parameters
	  ----------
	  x, y: float
	      Input numbers to sum
	  print: bool
	      If true, print a message

	  """

	  if print:
	      print("Message!")
	  return x + y

4. Name variables sensibly. Avoid using single-letter variables, it is better to name something ``power_spectral_density_array`` than ``psda``.
5. Don't repeat yourself. If code is repeated in multiple places, wrap it up into a function.
6. Add tests. The CI is there to do the work of "checking" the code, both now and into the future. Use it.

Merge requests
--------------

All changes to the code base go through the `merge-request workflow <https://docs.gitlab.com/ee/user/project/merge_requests/>`_ Anyone may
review your code and you should expect a few comments and questions.
Once all discussions are resolved, core developers will approve the merge request and then merge it into the master branch.
If you go a few days without a reply, please feel free to ping the thread by adding a new comment.

All merge requests should be focused: they should aim to either add one feature, solve one bug, or fix some stylistic issues.
If multiple changes are clumped together it can slow down the process and make it harder to review.

Before you begin: we highly recommend starting by opening an issue laying out what you want to do, especially if your change will be a significant amount of work to write.
This lets a conversation happen early in case other contributors disagree with what you'd like to do or have ideas that will help you do it.

Comments and questions may pertain to the functionality, but they may also relate to the code quality.
We are keen to maintain a high standard of the code.
This makes it easier to maintain, develop, and track down buggy behaviour.
See the Code Style section for an overview.

Reviewing Changes
~~~~~~~~~~~~~~~~~

If you are reviewing a merge request (either as a core developer or just as an
interested party) please keep these three things in mind

* If you open a discussion, be timely in responding to the submitter. Note, the
  reverse does not need to apply.
* Keep your questions/comments focused on the scope of the merge request. If
  while reviewing the code you notice other things which could be improved,
  open a new issue.
* Be supportive - merge requests represent a lot of hard work and effort and
  should be encouraged.

Reviewers should follow these rules when processing merge requests:

* Always wait for tests to pass before merging MRs.
* Delete branches for merged MRs (by core devs pushing to the main repo).
* Make sure related issues are linked and (if appropriate) closed.
* Squash commits

Typical workflow
----------------

Asimov uses the fork and merge model for code review and contributing to the
repository. As such, you won't be able to push changes to the master branch.
Instead, you'll need to create a fork, make your changes on a feature branch,
then submit a merge request. The following subsections walk you through how to
do this. 

Step a) getting started
~~~~~~~~~~~~~~~~~~~~~~~

All the code lives in a git repository (for a short introduction to git, see
`this tutorial <https://docs.gitlab.com/ee/gitlab-basics/start-using-git.html>`_)
which is hosted here: https://git.ligo.org/asimov/asimov.  If you haven't
already, you should
`fork <https://docs.gitlab.com/ee/gitlab-basics/fork-project.html>`_ the
repository and clone your fork, i.e., on your local machine run

.. code-block:: console
		
		$ git clone git@git.ligo.org:albert.einstein/asimov.git


replacing the SSH url to that of your fork. This will create a directory
`/asimov` containing a local copy of the code. From this directory, you can run

.. code-block:: console
		
		$ pip install -e .
		

which will install `asimov` using the python package installer `pip`.  The `-e`
argument will mean that when you change the code your installed version will
automatically be updated.

Step b) Updating your fork
~~~~~~~~~~~~~~~~~~~~~~~~~~

If you already have a fork of asimov, and are starting work on a new project you
can link your clone to the main (`asimov`) repository and pull in changes that
have been merged since the time you created your fork, or last updated:

**Link your fork to the main repository:** from the directory `/asimov`
containing a local copy of the code:

.. code-block:: console
		
		$ git remote add upstream https://git.ligo.org/asimov/asimov

You can see which "remotes" you have available by running

.. code-block:: console
		
		$ git remote -v

**Fetch new changes from the `asimov` repo:**

.. code-block:: console
		
		$ git pull asimov master


Step c) Creating a new feature branch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All changes should be developed on a feature branch, in order to keep them
separate from other work, simplifying review and merging once the work is done.
To create a new feature branch:

.. code-block:: console
		
		$ git pull asimov
		$ git checkout -b my-new-feature asimov/master


Step d) Hack away
~~~~~~~~~~~~~~~~~

1. Develop the changes you would like to introduce, using `git add` to add files with changes. Ideally commit small units of change often, rather than creating one large commit at the end, this will simplify review and make modifying any changes easier.
2. Commit the changes using `git commit`. This will prompt you for a commit message. Commit messages should be clear, identifying which code was changed, and why. Common practice (see e.g. `this blog <https://chris.beams.io/posts/git-commit/)>`_ is to use a short summary line (<50 characters), followed by a blank line, then more information in longer lines.
3. Push your changes to the remote copy of your fork on git.ligo.org

.. code-block:: console

	$ git push origin my-new-feature

**Note:** For the first `push` of any new feature branch, you will likely have
to use the `-u/--set-upstream` option to `push` to create a link between your
new branch and the `origin` remote:

.. code-block:: console
		
		$ git push --set-upstream origin my-new-feature

Step e) Open a Merge Request
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you feel that your work is finished, or if you want feedback on it, you
should create a Merge Request to propose that your changes be merged into the
main (`asimov`) repository.

After you have pushed your new feature branch to `origin`, you should find a
new button on the `asimov repository home page <https://git.ligo.org/asimov/asimov>`_ inviting you to create a Merge
Request out of your newly pushed branch.  You should click the button, and
proceed to fill in the title and description boxes on the MR page. If you are
still working on the merge request and don’t want it to be merged accidentally,
add the string "WIP", "work in progress" or "do not merge" (not
case-sensitive), to the title.

Once the request has been opened, one of the maintainers will assign someone to
review the change.

Hints and tips
--------------

Licence
~~~~~~~

When submitting a MR, please don't include any license information in your
code. Our repository is
`licensed <https://git.ligo.org/asimov/asimov/blob/master/LICENSE.md>`_. When
submitting your merge request, we will assume you have read and agreed to the
terms of `the
license <https://git.ligo.org/asimov/asimov/blob/master/LICENSE.md>`_.

Removing previously installed versions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have previously installed `asimov` using `pip` (or generally find buggy
behaviour), it may be worthwhile purging your system and reinstalling. To do
this, first find out where the module is being imported from: from any
directory that is *not* the source directory, do the following

.. code-block:: console
		
		$ python
		>>> import asimov
		>>> print(asimov.__file__)
		/home/user/anaconda2/lib/python2.7/site-packages/asimov-0.2.2-py2.7.egg/asimov/__init__.pyc

In the example output above, we see that the directory that module is installed
in. To purge our python installation, run

.. code-block:: console
		
		$ rm -r /home/user/anaconda2/lib/python2.7/site-packages/asimov*


You can then verify this was successful by trying to import asimov in the python interpreter.

Attribution
-----------

This contributing guide was heavily influenced (and borrows components from) the Bilby contributions guide.
