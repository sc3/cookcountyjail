[![Build Status](https://travis-ci.org/sc3/cookcountyjail.svg?branch=master)](https://travis-ci.org/sc3/cookcountyjail)

# Cook County Jail Data Project

We have built an API that tracks the population of Cook County Jail over time and summarizes trends, the workin version of which is running at http://cookcountyjail.recoveredfactory.net. We are also working on a newer version to supplement and eventually replace the one currently available. 

Our whole application has three essential components: **(1) the aforementioned API**, **(2) the database** that backs the API, and **(3) the web scraper** that populates the database. 


### Our Data

Each day, our web scraper runs and updates our database of inmate information; personally identifying information is not kept. Over time, we have uncovered a lot of potentially interesting data that can be used to analyze trends in the Cook County Jail System, though it is not definitive. For a basic look at some of these trends, see our sister project, [26th and California](http://26thandcalifornia.recoveredfactory.net/v1.0/) and the code that backs it: https://github.com/sc3/26thandcalifornia.  

If you are interested in exploring or otherwise using the raw data from our API, see our [API Guide](https://github.com/sc3/cookcountyjail/wiki/API-guide) on what data is available, and the best way to access it. There is also a small [v2.0 API Guide](https://github.com/sc3/cookcountyjail/wiki/API-2.0-Guide), which is still growing. While this is being developed, you can influence the choice of what API methods are built next by leaving a comment on the [2.0 API Hackpad](https://freegeekchicago.hackpad.com/Cook-Count-Jail-2.0-API-Requests-and-Ideas-for-Functionality-BbMobFdtEKu).


### Contributing

Want to help out? There's a lot of ways you can contribute.

- by reporting bugs
- by suggesting new features
- by translating to a new language
- by writing or editing documentation
- by writing code (no patch is too small: fix typos, add comments, clean up inconsistent whitespace)
- by refactoring code
- by closing issues
- by reviewing patches

If you want to contribute to the development of the project itself, please see our [wiki page on getting started](https://github.com/sc3/cookcountyjail/wiki/Contributing).


### Our Issues

We use GitHub's issue tracker to report problems and to coordinate development efforts.

Here's a list of issues that are **self-contained and need someone to tackle them**:  
https://github.com/sc3/cookcountyjail/issues?labels=ready&state=open. 

And here's another, for **things people are currently working on**:  
https://github.com/sc3/cookcountyjail/issues?labels=in+progress&state=open.
    
    
### Contributors
    
See [AUTHORS.md](https://github.com/sc3/cookcountyjail/blob/master/AUTHORS.md) for our list of contributors.

### License

Licensed under the GNU General Public License Version 3.
See [LICENSE.md](https://github.com/sc3/cookcountyjail/blob/master/LICENSE.md).
