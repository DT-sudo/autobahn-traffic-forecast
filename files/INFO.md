Hackathon Team Guide

Hi everyone! 👋

This document explains how we will use Claude, organize our development workflow, communicate with mentors and judges, prepare the technical prototype, and deliver the final presentation.

The purpose of this guide is to make our work predictable and efficient. Nobody is expected to know everything from the beginning. We will divide the work, ask questions, test ideas, and improve the project together.

⸻

1. Claude Usage Guidelines

Claude can be extremely useful during the hackathon, but its usage limits can be consumed surprisingly quickly. We should therefore use the available models carefully.

Communicate with Claude in English

All project-related communication with Claude should be written in English.

This includes:

* research prompts;
* coding requests;
* debugging requests;
* architecture discussions;
* documentation generation;
* requests related to datasets;
* requests related to the prediction model;
* preparation of README files;
* preparation of presentation content.

Using one shared language will make it easier to:

* reuse prompts;
* share AI conversations;
* copy documentation into the repository;
* avoid inconsistent terminology;
* collaborate on generated code;
* prepare English-language project materials.

Prompts, generated documentation, variable names, comments, API descriptions, and technical explanations should preferably be written in English.

Recommended model usage

Use Haiku for:

* general research;
* learning an unfamiliar topic;
* summarizing documentation;
* generating basic ideas;
* simple coding questions;
* preparing drafts;
* tasks that are not directly related to the final project implementation.

Haiku is still a capable model, but it usually consumes significantly fewer resources.

Use Sonnet 4.6 for:

* tasks directly related to our project;
* architecture decisions;
* implementing important project components;
* generating the prediction pipeline;
* debugging difficult problems;
* analyzing project-specific code;
* improving the final solution.

For normal project work, keep the effort setting at Medium or lower.

Higher effort settings should only be used when we encounter a genuinely difficult problem that cannot be solved efficiently with the standard settings.

Avoid unnecessary Deep Research

Do not use Sonnet 4.6 with Deep Research for ordinary research questions.

Deep Research and high-effort Sonnet requests can consume the available limits very quickly. Start with:

1. Haiku;
2. low or medium effort;
3. another AI tool, when appropriate.

Useful results from other tools can later be saved as Markdown files and imported into Claude as project context.

⸻

2. Important: What to Do When Claude Shows a Network Error

Claude may occasionally show a network or connection error after you submit a prompt.

You may see a notification in the upper-right corner suggesting that you submit the prompt again.

Do not immediately resubmit the prompt

Even when Claude appears not to have processed the request, the attempt may still consume part of the usage limit.

Submitting the same prompt several times can therefore waste a significant amount of the available quota.

Use this procedure instead

When a prompt appears to fail:

1. Do not press the retry button.
2. Open another chat from the left sidebar.
3. Return to the original chat.
4. Let the conversation reload.
5. Check whether the answer has appeared.

In many cases, Claude has already processed the request, but the interface failed to display the response correctly.

Why this matters

The probability and cost of these errors may become more noticeable when using:

* stronger models;
* higher effort settings;
* long prompts;
* Deep Research;
* complex tasks.

During testing, repeatedly submitting one failed prompt with maximum settings consumed almost half of the available five-hour usage limit while producing only one useful response.

Please be careful and avoid unnecessary retries.

⸻

3. Subscription and Usage Limits

A shared Claude Team subscription is currently intended for teams of at least five people.

Since our team has four members, each person should use an individual Claude Pro subscription.

You can monitor your current limits here:

Settings → Usage

Check this page regularly, especially before starting a large or complex task.

⸻

4. Repository and Collaboration

We will work in one shared Git repository.

The repository should be the main source of truth for:

* source code;
* project documentation;
* useful prompts;
* API descriptions;
* configuration instructions;
* architecture decisions;
* prediction-model documentation;
* dataset download instructions;
* presentation materials;
* important research notes.

Avoid keeping essential information only inside private AI chats. If something is important for the team, add it to the repository in a clear Markdown file.

Basic collaboration rules

Before starting work:

1. Check the current state of the repository.
2. Pull the latest changes.
3. Make sure nobody else is already working on the same task.
4. Create a separate branch when appropriate.
5. Keep commits small and understandable.
6. Tell the team when an important feature or change is ready.

Do not rewrite or remove another person’s work without discussing it first.

⸻

5. What We Are Expected to Build

We are not expected to create a complete production-ready system during the hackathon.

The objective is to demonstrate a working prototype that:

* solves one clearly defined problem;
* uses the provided data;
* applies understandable processing or prediction logic;
* produces a measurable or visible result;
* can be demonstrated through a simple interface.

A typical project flow may look like this:

Data
  ↓
Data validation and preprocessing
  ↓
Prediction model or algorithm
  ↓
API or backend
  ↓
Simple user interface
  ↓
Visible and measurable result

The prototype does not need to be perfect.

It needs to be:

* understandable;
* demonstrable;
* relevant to the challenge;
* visually convincing;
* stable enough for a short live demonstration.

⸻

6. Think Like the Target User

Our target users - the jury are likely to be marketers rather than software engineers.

They may not be especially interested in:

* which programming language we used;
* how complex our backend is;
* how many services are running;
* how sophisticated the internal architecture looks;
* which exact machine-learning library produced the prediction.

They will be much more interested in:

* what problem we solve;
* why the problem matters;
* how our product improves their work;
* how much time or money it can save;
* what measurable result it produces;
* whether the solution is simple to understand and use;
* whether the prediction helps them make a better decision.

We should treat the project as a product that we need to present and sell.

The technical implementation is important, but it should support the product story rather than replace it.

⸻

7. Finding the Right Problem

The most important early task is not writing code.

It is identifying the exact problem that the judges and potential users care about.

We should learn this from:

* the official challenge description;
* the provided data;
* conversations with the organizers;
* mentor consultations;
* feedback from the judges;
* carefully prepared questions.

We should not assume that our first interpretation of the challenge is correct.

A technically impressive solution can still fail if it solves the wrong problem.

Questions we should be able to answer

* Who is the user?
* What is their current workflow?
* What is slow, expensive, repetitive, or confusing?
* What result do they want?
* How do they currently solve the problem?
* What prevents them from solving it effectively?
* What would make them trust our solution?
* What prediction or recommendation would actually help them?
* What result can we realistically demonstrate during the hackathon?
* How can we measure the improvement?

Our goal is to find the core pain point and build the simplest convincing solution around it.

⸻

8. Build the Website Structure First

The first practical implementation task should be creating the basic website structure.

Do not begin by trying to implement every backend component, prediction feature, and integration at the same time.

Start by defining the main blocks of the product:

* landing or welcome section;
* data input or upload section;
* configuration controls;
* processing or analysis state;
* prediction result;
* explanation or recommendation;
* metrics or comparison;
* call to action or next step.

The initial website can work with:

* static data;
* mock responses;
* predefined examples;
* temporarily simulated backend logic.

The purpose of the first version is to show how the complete product should work from the user’s perspective.

Once the main user flow is visible, we can gradually connect:

* real data;
* preprocessing;
* prediction logic;
* backend endpoints;
* additional visualizations;
* error handling.

This approach gives us a usable product skeleton early and prevents the team from building disconnected technical components.

⸻

9. First-Day Objective

We should have something visible and discussable as early as possible.

Ideally, during the first part of the first day, we should already have:

* a clear problem statement;
* a proposed user flow;
* the main website structure;
* a basic interface prototype;
* mock data or simulated results;
* an explanation of the planned prediction logic;
* a list of assumptions;
* a list of technical or product bottlenecks;
* specific questions for the mentors and judges.

The backend does not need to be complete at this stage.

A basic interface with partially simulated logic is enough to make the concept understandable and receive meaningful feedback.

Why we should build the interface immediately

The earlier we have a visible prototype, the earlier we can approach mentors.

This is important because mentors may:

* become busy with other teams;
* be less available later;
* leave before the end of the working day;
* have limited time for detailed feedback.

We should aim to be among the first teams to approach them with something concrete.

Without a prototype, discussions may remain too abstract. With a visible prototype, mentors and judges can tell us:

* what they understand;
* what they do not understand;
* what seems useful;
* what seems unnecessary;
* what should be changed;
* which result would be most impressive;
* whether the prediction solves a real marketing problem.

⸻

10. Building the Initial UI

Tools such as Lovable can generate a basic interface very quickly when the prompt and user flow are clear.

The difficult part is not generating the interface.

The difficult part is deciding:

* what the user should see;
* what action the user should perform;
* what input the system requires;
* what result the system should display;
* how the prediction should be explained;
* why that result is valuable.

With a clear concept and a well-written English prompt, an initial UI prototype can often be generated in a few minutes.

Do not worry about visual perfection during the first iteration. The initial purpose of the interface is to communicate the idea and collect feedback.

Build the main blocks first. Add visual polish, real data, backend integration, and secondary features later.

⸻

# 11. Prediction Model and .joblib File

The project will include a prediction component based on a previously trained model.

The most important distinction is that model preparation and model usage are two separate stages.

## Stage 1 — Model preparation before running the final application

Before the final application is started, we will:

1. load the raw dataset;
2. clean and preprocess the data;
3. prepare the required features;
4. train the prediction model;
5. evaluate its quality;
6. export the final trained pipeline into a .joblib file.

This work is performed in advance.

The training code must remain in the repository so that we can explain how the model was created and reproduce it if necessary. However, the final application will not train or evaluate the model during normal execution.

The final application will use only the already generated .joblib file.

The preparation workflow is:

text Raw dataset   ↓ Cleaning and preprocessing   ↓ Feature transformation   ↓ Model training   ↓ Model evaluation   ↓ Export of the completed pipeline to .joblib 

## Stage 2 — Model usage in the final application

The .joblib file must already exist before Docker and the final application are started.

The runtime workflow is:

text Preprocessed input data   ↓ Already exported .joblib file available before Docker starts   ↓ Loading the .joblib model in the backend   ↓ Prediction performed directly through the loaded joblib object   ↓ Displaying the result in the application 

The final program must not:

- train the model;
- evaluate the model;
- rebuild the prediction pipeline;
- process the complete training dataset;
- generate a new .joblib file during startup.

It should only:

1. load the existing .joblib file;
2. prepare the user's input in the expected format;
3. pass the input to the loaded model;
4. receive the prediction;
5. display the result.

For example:

python import joblib  model = joblib.load("models/prediction_pipeline.joblib") prediction = model.predict(input_data) 

There is no need to create a separate prediction API solely for this purpose. The backend can load the .joblib file and use it directly.

## What should be included in the .joblib file

Whenever possible, the .joblib file should contain the entire prepared prediction pipeline rather than only the final estimator.

The exported object should ideally include:

- preprocessing logic;
- categorical encoders;
- feature scaling;
- missing-value handling;
- feature ordering;
- the trained model;
- all transformations required before prediction.

This is important because the final application should not manually reproduce the preprocessing that was used during model training.

The goal is to make runtime prediction as simple and reliable as possible:

python model = joblib.load("models/prediction_pipeline.joblib") prediction = model.predict(input_data) 

## Ask Claude to generate the model-preparation code

When asking Claude to create the model-preparation component, provide:

- the dataset structure;
- column names;
- the target variable;
- the expected prediction type;
- possible missing values;
- categorical columns;
- numerical columns;
- evaluation requirements;
- the expected location and name of the .joblib file.

Ask Claude to generate code that:

1. loads the training dataset;
2. validates the required columns;
3. cleans and preprocesses the data;
4. performs feature transformation;
5. trains the model;
6. evaluates the model;
7. exports the complete trained pipeline to a .joblib file;
8. includes clear error messages;
9. uses a fixed random seed where applicable;
10. documents all required dependencies;
11. can be executed separately before Docker is started.

This code must be preserved in the repository for reproducibility and explanation.

However, it is not part of the normal runtime workflow. We will primarily use the .joblib file produced by this code.

## Require a model contract Markdown file

Together with the .joblib generation code, ask Claude to create a separate Markdown document describing exactly how the saved model must be used.

A suitable filename is:

text MODEL_CONTRACT.md 

This document must explain:

- the path to the .joblib file;
- the expected input format;
- required input fields;
- optional input fields;
- expected data types;
- accepted values;
- expected units;
- handling of missing values;
- expected feature or column order, when relevant;
- preprocessing already included in the .joblib pipeline;
- preprocessing that must still be performed by the backend, if any;
- an example input;
- the prediction output format;
- possible prediction values;
- probability or confidence format, when available;
- possible errors;
- the model version;
- a minimal model-loading example;
- a minimal prediction example.

Example structure:

markdown # Model Contract  ## Model File  `models/prediction_pipeline.joblib`  The model is trained and exported before the final application is started.  The application must load this existing file. It must not train or recreate the model during startup.  ## Expected Input  | Field | Type | Required | Description | |---|---|---:|---| | campaign_budget | float | Yes | Campaign budget in EUR | | channel | string | Yes | Marketing channel | | impressions | integer | Yes | Number of impressions |  ## Example Input  json
{
  "campaign_budget": 5000.0,
  "channel": "social_media",
  "impressions": 120000
}
 ## Loading the Model python
import joblib

model = joblib.load("models/prediction_pipeline.joblib")
 ## Running a Prediction python
prediction = model.predict(input_data)
 ## Expected Output json
{
  "prediction": 0.74,
  "label": "high_performance",
  "confidence": 0.86
}
 

This file will serve as a contract between:

- the code that originally trains and exports the model;
- the saved .joblib pipeline;
- the backend that loads the model;
- the frontend that displays the result;
- the team members working on integration.

Nobody should have to guess what the .joblib file expects or what it returns.

## Validate the generated .joblib file

Before adding the model to Docker and the final application:

1. generate the .joblib file in advance;
2. load it in a separate clean test script;
3. send a valid example input;
4. verify the prediction;
5. test missing required fields;
6. test incorrect data types;
7. test unknown categorical values;
8. confirm that feature order is handled correctly;
9. check that runtime input matches MODEL_CONTRACT.md;
10. verify that the model can be loaded from the path used inside Docker.

Do not wait until final integration to discover that the saved model expects a different input format.

The .joblib file must be ready, tested, and available before Docker is started.

---

# 12. Working With Large Datasets

The datasets used in this project will be large.

They must not be committed directly to GitHub.

We will store the required datasets on Google Drive as downloadable archives.

The datasets used by the final project will most likely be:

- cleaned;
- preprocessed;
- reorganized;
- merged when necessary;
- converted into the required format;
- placed into the directory structure expected by the project.

The archived dataset on Google Drive should contain the already prepared files required by the project.

The final application should not need to repeat the complete cleaning and preparation process every time it starts.

## Do not push datasets to GitHub

The datasets are too large to be stored in the Git repository.

Committing them could:

- exceed GitHub file-size limits;
- make cloning the repository extremely slow;
- unnecessarily increase the repository size;
- leave large files permanently inside Git history;
- create problems for every team member.

Dataset directories and dataset archives must be added to .gitignore.

For example:

gitignore data/raw/ data/processed/ data/training/ data/external/ *.csv *.parquet *.zip *.tar.gz 

Specific small example files may be committed when they are required for demonstration or testing.

## Store the prepared datasets on Google Drive

The final prepared datasets should be archived and uploaded to Google Drive.

For example:

text hackathon-prepared-dataset.zip 

The archive should contain the exact structure expected by the project.

For example:

text data/ ├── processed/ ├── prediction_input/ ├── training/ └── examples/ 

The dataset archive should already contain the cleaned and prepared data required by the application and model-development scripts.

## Add dataset installation commands to the README

The README must contain tested commands that:

1. download the dataset archive from Google Drive;
2. create the required directories;
3. extract the archive;
4. place the dataset files into the expected project locations;
5. remove the archive after extraction, when appropriate;
6. verify that the required files exist.

Example:

bash mkdir -p data  gdown "GOOGLE_DRIVE_FILE_ID" -O hackathon-prepared-dataset.zip  unzip hackathon-prepared-dataset.zip -d .  rm hackathon-prepared-dataset.zip 

The actual commands must be tested before submission.

The README must also specify:

- the expected dataset directory structure;
- the name of each important dataset;
- the approximate archive size;
- the approximate extracted size;
- required tools such as gdown and unzip;
- the dataset version;
- the expected file formats;
- whether the data is cleaned, transformed, or aggregated;
- which dataset is used for model preparation;
- which small sample data is used by the final demonstration.

## Preserve the preparation code

Even though the final prepared datasets will be downloaded from Google Drive, we should preserve the code used to create them.

For example:

text scripts/ ├── download_data.sh ├── clean_data.py ├── prepare_features.py └── train_and_export_model.py 

These scripts are important for:

- reproducibility;
- explaining our technical process;
- rebuilding the datasets if necessary;
- demonstrating how the .joblib file was created.

However, the final application will normally use:

- the already prepared dataset files;
- the already generated .joblib file.

It will not repeat the complete dataset-cleaning, model-training, or model-evaluation process during startup.
⸻

13. Communicating With Judges and Mentors

A major part of the hackathon will be gathering information from the judges, mentors, and challenge representatives.

We should actively talk to them rather than waiting until the final presentation.

Prepare to ask focused questions such as:

* Who is the primary user of this solution?
* What is the most expensive part of the current workflow?
* Which problem should we prioritize?
* Which result would be the most valuable to demonstrate?
* What data fields are reliable?
* Are there any restrictions on using the provided data?
* What would make this solution realistic for an actual company?
* Which metric would best prove that the solution works?
* What would make you choose one project over another?
* Is our current interpretation of the challenge correct?
* What is missing from our prototype?
* Which feature should we remove or simplify?
* What kind of prediction would be genuinely useful?
* How should the prediction be explained to a non-technical user?

Avoid asking only broad questions such as:

“What do you think about our idea?”

Instead, show a specific prototype or workflow and ask concrete questions.

For example:

“Our prototype predicts which campaigns are likely to underperform and recommends the next action. Would this be more valuable to marketers as a dashboard, a weekly report, or an integration with their existing tools?”

The more specific the question is, the more useful the answer will be.

⸻

14. Prototype Strategy

The safest hackathon strategy is to build one complete and understandable workflow rather than many unfinished features.

A strong prototype may demonstrate:

1. The user provides or selects some data.
2. The system validates and processes the data.
3. The model produces a prediction.
4. The result is displayed clearly.
5. The interface explains what the prediction means.
6. The product recommends an action.
7. The project shows a measurable improvement.

Examples of measurable results include:

* time saved;
* increased conversion potential;
* reduced manual work;
* improved targeting accuracy;
* faster content analysis;
* fewer irrelevant recommendations;
* better campaign prioritization;
* clearer customer segmentation.

Some parts of the demonstration may use prepared or simulated data when necessary, but the team must understand how the real implementation would work and be able to explain the limitations honestly when asked.

We should never depend on claims that we cannot reasonably defend during questions.

⸻

15. Feature Prioritization

The final product should focus on the features that directly answer what the judges want.

Do not try to demonstrate every feature we implemented.

Before deciding what to show, ask:

* Which feature solves the main problem?
* Which feature is easiest to understand?
* Which feature produces the strongest visible result?
* Which feature did the mentors react to most positively?
* Which feature supports the main business value?
* Which feature can be demonstrated reliably?
* Which feature can be explained in one sentence?

The main features should receive most of the:

* development time;
* interface space;
* presentation time;
* demo attention;
* visual polish.

Secondary features should not distract from the central value proposition.

It is better to present one feature extremely clearly than five features superficially.

⸻

16. Final Presentation

The final presentation will likely be very short.

It may be approximately three minutes, although the exact time depends on the rules announced by the organizers.

Treat the time limit as strict

As soon as the official time limit is known, prepare the presentation for that exact duration.

We must be completely confident that we can finish within the allowed time.

If the limit is three minutes, the presentation should consistently finish in less than three minutes during rehearsal.

Do not prepare a five-minute presentation and assume that it can be delivered faster under pressure.

Speaking usually becomes:

* less structured;
* slower;
* more repetitive;
* more stressful

during the actual presentation.

Therefore, keep a safety margin.

For a three-minute limit, aim for approximately:

2 minutes 30 seconds 

This leaves time for:

* slide transitions;
* short pauses;
* technical delays;
* audience reactions;
* an unexpected interruption.

Focus on the main features

The presentation should emphasize:

* the exact problem the judges care about;
* the strongest feature;
* the user value;
* the prediction or recommendation;
* the visible result;
* the measurable impact.

Do not spend valuable presentation time explaining internal technical details unless they are essential to understanding the value.

The judges should quickly understand:

1. who has the problem;
2. why the problem matters;
3. what our product does;
4. what the prediction means;
5. why our solution is useful;
6. what result we achieved.

Recommended slide count

For a three-minute presentation, use approximately five or six slides, including the opening and closing slides.

For a slightly longer presentation, use no more than six or seven slides.

Opening and closing slides should not contain critical information that requires a long explanation.

Recommended structure

Slide 1 — Project name and value proposition

* Team name
* Product name
* One-sentence value proposition

Slide 2 — The problem

* Who experiences the problem?
* Why does it matter?
* What is inefficient about the current process?

Slide 3 — Our solution

* What the product does
* The main feature
* Why the prediction or recommendation is valuable

Slide 4 — Live demonstration

Show one complete user journey:

Input → Processing → Prediction → Recommended action

Slide 5 — Measurable impact

Examples:

* analysis reduced from hours to minutes;
* manual steps reduced;
* campaigns prioritized automatically;
* recommendations generated from real data;
* clearer and faster marketing decisions.

Slide 6 — Conclusion

* Restate the main value
* Mention the next realistic development step
* Thank the audience

⸻

17. Presentation Rehearsal

Do not assume that the presentation will fit the time limit without testing it.

Rehearse it several times with a timer.

At least one rehearsal should include:

* the actual slide deck;
* the actual live demo;
* the person who will present;
* the same device that will be used;
* realistic transitions;
* the backup plan.

During rehearsal, remove:

* repeated explanations;
* unnecessary technical details;
* secondary features;
* long introductions;
* weak slides;
* anything that does not support the central story.

The presenter should know which parts can be skipped immediately if something takes longer than expected.

⸻

18. Demo Reliability

The live demonstration should be short, controlled, and repeatable.

Prepare:

* one reliable input example;
* one expected output;
* a backup screenshot or recording;
* locally available sample data;
* a clear explanation in case an external service fails.

Do not make the final demonstration dependent on:

* an unstable external API;
* an unreliable network connection;
* a long AI generation process;
* model training during the presentation;
* downloading a large dataset;
* unpredictable user input.

The .joblib model should already be trained and ready to load.

Whenever possible, prepare the expected result in advance while still keeping the prototype interactive enough to show the core workflow.

⸻

19. Reserve Time for Finalization

Do not continue adding features until the last minute.

Cleaning and preparing the final project can take much longer than expected.

Reserve at least three hours before the submission deadline for finalization.

Depending on the project state, even three hours may be barely enough.

Finalization includes

* removing unnecessary files;
* removing temporary code;
* deleting unused components;
* checking .gitignore;
* removing secrets and API keys;
* cleaning the repository structure;
* checking installation commands;
* testing the project from a clean environment;
* testing dataset download commands;
* testing .joblib loading;
* updating MODEL_CONTRACT.md;
* writing and polishing the README;
* checking screenshots;
* preparing the presentation;
* rehearsing the presentation;
* preparing the backup demo;
* checking all links;
* making the final submission.

Stop adding features early enough

Before the reserved finalization period begins:

1. freeze the main feature set;
2. merge stable branches;
3. stop unnecessary experiments;
4. decide which features will be shown;
5. focus only on fixing critical issues.

A smaller polished project is much stronger than a larger project that is difficult to run, understand, or demonstrate.

⸻

20. README Requirements

The README should allow another person to understand and run the project without contacting us.

It should include:

* project name;
* short product description;
* problem statement;
* target user;
* main features;
* screenshots;
* architecture overview;
* technology stack;
* prerequisites;
* installation instructions;
* environment-variable instructions;
* dataset download commands;
* expected dataset structure;
* model setup;
* instructions for generating the .joblib file;
* instructions for starting the backend;
* instructions for starting the frontend;
* example usage;
* known limitations;
* team members.

The commands in the README must be tested.

Do not include instructions that only work on the computer of the person who wrote them.

⸻

21. Suggested Project Structure

A possible repository structure is:

project/
├── backend/
│   ├── app/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   └── package.json
├── data/
│   ├── raw/
│   ├── processed/
│   └── examples/
├── models/
│   └── prediction_pipeline.joblib
├── scripts/
│   ├── download_data.sh
│   ├── clean_data.py
│   ├── build_features.py
│   └── train_model.py
├── docs/
│   ├── MODEL_CONTRACT.md
│   └── ARCHITECTURE.md
├── presentation/
├── .env.example
├── .gitignore
└── README.md

The exact structure may change, but responsibilities should remain clear.

⸻

22. Team Priorities

When deciding what to work on, use the following order:

1. Understand the challenge.
2. Identify the target user.
3. Define one important problem.
4. Create the main website structure.
5. Add mock data and a visible user flow.
6. Approach mentors as early as possible.
7. Confirm the problem and priorities.
8. Prepare and document the data.
9. Build the prediction pipeline.
10. Export and validate the .joblib file.
11. Document the model interface.
12. Connect the backend and frontend.
13. Produce a measurable result.
14. Stabilize the demonstration.
15. Freeze the feature set.
16. Reserve at least three hours for finalization.
17. Prepare and rehearse the presentation.

Do not spend the majority of the hackathon improving technical details that the user cannot see and that do not improve the demonstration.

⸻

23. Final Reminder

Nobody needs to build everything alone, and nobody is expected to understand every technology immediately.

When something is unclear:

* ask the team;
* write down the uncertainty;
* create a small test;
* ask a mentor a specific question;
* use the simplest suitable AI model;
* communicate with Claude in English;
* document the useful result.

Our goal is not to create the largest or most technically complicated system.

Our goal is to create the clearest, most useful, and most convincing prototype within the available time.

Build the visible product structure early, talk to mentors before they become unavailable, focus on what the judges actually want, and leave enough time to polish everything before submission.

Stay calm, communicate openly, and focus on the problem we are solving. 🚀