---
title: "Homework 7"

output: rmarkdown::github_document
---

```{r setup, include=FALSE, echo = F}
knitr::opts_chunk$set(echo = TRUE, fig.align = "center")
library(tidyverse)
library(ggplot2)
library(maps)
options(scipen=999)
```

Date: November 29, 2020  
CS 625, Fall 2020 

# Generating Questions from Real-World Data
For this homework, I will be working with the dataset related to the covid-19 U.S. County-Level Data from state and local governments and health departments. In this report, I will be generating my questions for this dataset. The main objective of this assignment is for me to visualize the complete record of the outbreak of covid-19. In order to obtain better visualization, I will also use a county dataset from library maps.

## Datasets Description

I will be using two datasets. One is from the New York Times and the other one comes from the library maps. I will analyze the first dataset and combine the two datasets to create more decent visualization. 

### Dataset 1: dataset - the covid-19 U.S. County-Level Data 
*source:  URL: https://github.com/nytimes/covid-19-data*  

From the data source, there are three datasets. I picked to work with the us-counties.csv since I am interested in studying the covid-19 in the counties in Massachusetts. There are 777720 observations in the original dataset. In order to select the target sub dataset, I obtained the dataset of Massachusetts. In the sub dataset, there are 3949 observations. The detailed steps will be discussed in Data Clearning Sections in the EDA Process. 

![](img1.png)

*Figure 1 - The original dataset* 


### Dataset 2: dataset - County data of Massachusetts 

The source of the second dataset is from the maps packages. In order to combine with the first dataset, I used the filter to only export the county data of Massachusetts. 


## EDA process

### Initial Data Cleaning

#### Dataset: the covid-19 U.S. County-Level Data and MA county Data

Before analyzing the data, I used the filter funciton from the package tidyverse to export the targeted dataset by only selectig the data from Massachusetts. This sub dataset was used for further exploration.

**Cleaning Steps**  

  * I filtered the covid-19 county dataset by selecting the state which is equal to Massachusetts. I extracted 3949 observations from the original 777720 observations. 
  * I filtered the MA county data by selecting the subregion which is equal to Massachusetts. 

### Variables

#### Dataset 1: dataset - the covid-19 U.S. County-Level Data 

I used `str`function to demonstrate the structure of this dataset to better understand the dataset.

```{r}
# import covid-19 county dataset
covid_county <- read.csv("us-counties.csv", header = TRUE)

# select the counties in MA
covid_MA <- covid_county %>% 
  filter(state == "Massachusetts")

str(covid_MA)
```

Based on the above output, there is 3949 observations with 6 variables. I am interested in the variables `cases` and `deaths`. To know better of these two variables, I created two histograms to observe the distributions of the number of cases and deaths in MA.

```{r}
# histogram of cases and deaths
covid_MA %>% 
  ggplot() +
  aes(x = cases) +
  geom_histogram()
```

*Figure 2 - Histogram of the number of cases in MA* 


```{r}
covid_MA %>% 
  ggplot() +
  aes(x = deaths) +
  geom_histogram()
```

*Figure 3 - Histogram of the number of deaths in MA* 


#### Dataset 2: dataset - County data of Massachusetts 

I used `filter function to extract the MA county data from the package `maps` and use `str`function to demonstrate the structure of this dataset to better understand the dataset.

```{r}
# read MA couties dataset
MAcounties <- map_data("county") %>% 
  filter(region == "massachusetts")

str(MAcounties)
```

Based on the above output, there is 743 observations with 6 variables. I will use the variables `long` and `lat` to plot the map of MA. 

### Initial Detailed Questions (1 - After observing Variables and histograms)

After initially observing the variables in dataset 1, I have one question to come up with. To help the researcher to better understand the relationship between cases and deaths in MA. 
  * Is the number of deaths related to the number of cases in Massachusetts. 
  * Is there any pattern for each county?
  * Is the the number of deaths correlated with the number of cases for each county in MA? 

```{r}
covid_MA %>% 
  ggplot() +
  aes(x = cases, y = deaths) + 
  geom_point() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))
```

*Figure 4 - Scatter plot of the number of cases vs deaths in MA* 

```{r}
covid_MA %>% 
  ggplot() +
  aes(x = cases, y = deaths) + 
  geom_point() +
  facet_wrap(~county, scales = "free") +
  geom_smooth() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))
```

*Figure 5 - Scatter plot of the number of cases vs. deaths for each county in MA* 


Figure 2 and Figure 3 are wwo histograms which show the distributions of the cases and deaths in MA. From these two histograms, I can see that the two distributions look similar. There might be a correlation between the number of deaths and the number of cases. So I created a scatter plot to study their relationsip. According to Figure 4, it seems to be some relationship between the number of deaths and the number of cases in MA. However, it seems that there are different patterns due to there might be differences among counties. Therefore, I also created the scatter plot for each county (shown in Figure 5), considering that the number of deaths or cases may vary across counties. In addition, I also add a regression line to the scatter plots. From this scatter plot, I clearly see that there is a pattern between the number of deaths and the number of cases for each county in MA. Thus, the number of deaths correlated with the number of cases for each county in MA


### Initial Detailed Questions (2 - After observing the relation between deaths and cases in MA)

After checking the relationship between the number of deaths and the number of cases for each county in MA, I would like to see how county impacts the number of deaths and cases in MA. 

 * What is the impact of county on the number of cases or deaths in MA? 
 * Do the number of cases or deaths vary across counties in MA?

**Steps:** 

  * Use the `group_by` function to group the MA covid-19 data by county and summarise total number of deaths and total number of cases for each county in MA.
  * Use the group_by` function to group the MA covid-19 data by county and summarise the mean and median of the number of deaths and the number of cases for each county in MA.
  * Create two bar plots to display the total number of cases in a descending order and the total number of deaths in a descending order seperately.
  * Use the `gather` function to put the cases and deaths in the long foramt dataset and create one bar plot to show both the total number of cases and the total number of deaths.
  * Use the `reorder` funtion to order the the number of cases or death by median and create two boxplots to know how the number of cases or deaths vary across counties.
  
     
```{r}
# total deaths and cases in each county
dat1 <- covid_MA %>% 
  group_by(county) %>% 
  summarise(total_deaths = sum(deaths), total_cases = sum(cases))
dat1

# mean and median
covid_MA %>% 
  group_by(county) %>% 
  summarise(mean_deaths = mean(deaths), median_deaths = median(deaths),
            mean_cases = mean(cases), median_cases = median(cases))

```

```{r}
# display total cases in descending order
dat2 <- dat1
dat2$county <- factor(dat2$county, levels = dat2$county[order(-dat2$total_cases)])
dat2 %>% 
  ggplot() +
  aes(y = total_cases, x = county, fill = county) +
  geom_bar(stat = "identity") +
  ylab("Total Cases of Each County in MA") +
  xlab("County") +
  theme(plot.title = element_text(hjust = 0.5, size = 15),
        axis.title = element_text(size = 15),
        axis.text.x = element_text(angle = 45, hjust = 1))
```

*Figure 6 - Bar plot of the total number of cases for each county in MA* 


```{r}
# display total death in descending order
dat2$county <- factor(dat2$county, levels = dat2$county[order(-dat2$total_deaths)])
dat2 %>% 
  ggplot() +
  aes(y = total_deaths, x = county, fill = county) +
  geom_bar(stat = "identity") +
  ylab("Total Deaths of Each County in MA") +
  xlab("County") +
  theme(plot.title = element_text(hjust = 0.5, size = 15),
        axis.title = element_text(size = 15),
        axis.text.x = element_text(angle = 45, hjust = 1))
```

*Figure 7 - Bar plot of the total number of deaths for each county in MA* 


```{r}
# display total cases and death
dat3 <- dat1 %>% 
  gather(key = "Category", value = "Count", -county)

dat3 %>% 
  ggplot() +
  aes(x = county, y = Count, fill = Category) +
  geom_bar(position="dodge", stat="identity") +
  ylab("Count") +
  xlab("County") +
  theme(plot.title = element_text(hjust = 0.5, size = 15),
        axis.title = element_text(size = 15),
        axis.text.x = element_text(angle = 45, hjust = 1))
```

*Figure 8 - Bar plot of the total number of cases and deaths for each county in MA* 

```{r}
#  I am interested to know how cases or death vary across counties:
covid_MA %>% 
  ggplot() +
  aes(x = reorder(county, cases, FUN = median), y = cases) +
  geom_boxplot() +
  coord_flip() +
  xlab("Number of Cases") +
  ylab("County") 
```

*Figure 9 - Boxplot of the distribution of cases for each county in MA* 


```{r}
covid_MA %>% 
  ggplot() +
  aes(x = reorder(county, deaths, FUN = median), y = deaths) +
  geom_boxplot() +
  coord_flip() +
  xlab("Number of Deaths") +
  ylab("County")

```

*Figure 10 - Boxplot of the distribution of deaths for each county in MA* 

Firstly, I summarised the total number of deaths and cases for each county and the mean and median of the number of deaths and cases for each scounty. From the summary statistics, I can know the total nubmer, mean and median of the deaths and cases vary across counties in MA. Secondly, I graphed two bar plots to display the total number of cases in a descending order and the total number of deaths in a descending order seperately. As shown in Figure 6 & 7, I can clearly distinguish the total number of cases or deaths among different counties and I can easily tell which county has the maximum or minimum number of cases or deaths in MA. To compare the number of deaths and the number of cases, I also create a bar plot (as shown in Figure 8) to put both the deaths and cases for each county in one bar plot. Finally, I graphed two boxplots to compare the distributions of the cases or death for each county. I used reorder() function to reorder the county based on the median of the number of cases or death. As shown in Figure 9 & 10, I can clearly see the distribution difference among counties. Therefore, I can conclude that county has an impact on the number of cases or deaths in MA. In other words, the number of cases or deaths vary across counties in MA. 


### Initial Detailed Questions (3 - After checking the impact of county on the number of cases or deaths in MA)

  * How can visualize the data in the MA map? From the maps, can we distinguish the number of cases or death easily?
  
#### Merged Data


**Steps:** 

  * Remove the unknown data from the dataset 1 and add a new variable `subregion` in dataset 1, since there is no unknown county from dataset 2 and there is a variable `subregion`.
  * Add a new variable `id` to the dataset 1.
  * Combine the dataset 1 covid-19 data and dataset 2 MA county data using the `merge` function.
  * Use the `geom_polygon` function to plot a map.

```{r}
# remove unknown data
dat4 <- dat1 %>% 
  filter(county != "Unknown")
dat4$subregion <- c("barnstable", "berkshire", "bristol", "dukes", "essex", 
                    "franklin", "hampden", "hampshire", "middlesex", "nantucket", 
                    "norfolk", "plymouth", "suffolk", "worcester")

# add id 
dat4$id <- rownames(dat4)



# combine covid-19 data and MA county data
datnew <- merge(MAcounties, dat4, by = "subregion")
```


```{r}
ggplot() +
  geom_polygon(data = datnew, aes(x = long, y = lat, group = subregion, fill = total_cases)) +
  theme_void() +
  coord_map() +
  ggtitle("Number of Cases for each County in MA") 
```

*Figure 11 - Map for the number of cases for each county in MA* 

```{r}
ggplot() +
  geom_polygon(data = datnew, aes(x = long, y = lat, group = subregion, fill = total_deaths)) +
  theme_void() +
  coord_map() +
  ggtitle("Number of Deaths for each County in MA") 

```

*Figure 12 - Map for the number of cases for each county in MA* 

To help the researcher to better understand the differences of the number of cases or deaths for each county in MA, I plotted two maps which are shown in Figure 11 & 12: one map is for the cases occured in each county in MA and one map is for the deaths occured in each county in MA.  From these two plots, I realized to visualize the numbers of cases or deaths for each county in MA in a map.  The maps help us easily tell the differences among the counties in MA.


# References
https://github.com/nytimes/covid-19-data

https://tidyr.tidyverse.org/reference/gather.html

https://r4ds.had.co.nz/exploratory-data-analysis.html

https://geocompr.robinlovelace.net/adv-map.html

https://eriqande.github.io/rep-res-web/lectures/making-maps-with-R.html

