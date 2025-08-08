# Local Development 
#   setup
To setup your local dev environment, you'll need to create your environment variables 
1. Create a .secrets folder and add it to your gitignore file
2. Within the .secrets folder, save your GCloud private credentials (.json file). You can locate these from the GCloud console. Save it with whatever name you want
3. Create a .env file and populate it like so: 

    # .env
    DRIVER_PATH=the full path to chromedriver on your machine
    CREDENTIALS_PATH=the full path to the GCloud credentials .json file on your machine
    TABLE_ID=projects-portfolio-446806.jobs_scraping.linkedin_scraped_jobs

