# covid19-india

This is a (yet another) [interactive visualisation](https://covid19indiapd.herokuapp.com/) to track the trajectory of COVID-19 cases in Indian States. It is particularly perceptive in comparing how different states are doing with respect to each other and themseleves across time.

The growth rate (number of new cases) is plotted against the total number of confirmed cases. When both axes are plotted on a log scale, the n-day doubling line (exponential growth) becomes a straight line.

New cases in the past week were chosen to smooth out the noise in daily reporting. 
The size of the bubble indicates the current active cases. 

So, we want the bubbles to become smaller and go down sharply for victory!

## Inspiration
Minute Physics' [How To Tell If We're Beating COVID-19](https://youtu.be/54XLXg4fYsc) and Aatish Bhatia's [Covid Trends](https://aatishb.com/covidtrends/).

## Data Source
The underlying data is sourced from the crowdsourced database at [api.covid19india.org](https://api.covid19india.org/). The volunteers who maintain this API and the excellent [dashboard](https://www.covid19india.org/) deserve great applause.

## Credits
[Pramod Kasi](https://twitter.com/KasiPramod) and Disha Sarawgi

Created on Python using Plotly Dash. Hosted on Heroku.