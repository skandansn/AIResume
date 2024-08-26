AIResume has the power to pass ATS checks! 

Check out the front end app: https://airesume-frontend.onrender.com (might take some time to launch the servers after an idle time)

Demo creds: email:godskandan@gmail.com password:skandan

It can alter your resume to match with keywords that are expected for a specific job application.

Technologies used: NextJS for the front-end. FastAPI (Python) based back-end system.

Gemini AI for generative AI (generating updated resume)

Firebase and Firestore for data and file storage.

Flow:

Provide the job description to the API.

Optionally provide some manadatory keywords that has to be in the new updated resume.

Optinally provide some keywords that have to be ignored in the final resume.

Optionally specify which of your resumes to update (can store and use multiple different resume at a time)

AIResume finds the most important keywords for this job description and finds a way to add them to your resume.

Generate the final updated PDF version of your new resume.

Can also be used as an REST API: https://airesume-backend.onrender.com
