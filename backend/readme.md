
## Method 1: Using Swagger UI (EASIEST - No Coding!)

### Docker file - amanpr/hr-parser 
https://hub.docker.com/repository/docker/amanpr/hr-parser/general


### Step 1:The pulling of docker file### 
```bash
docker pull amanpr/hr-parser:latest
```

### Step 2: Run the docker file 
```
docker run -p 5000:8000 amanpr/hr-parser:latest
```



### Step 1: Start your server
```bash
python main.py
```

### Step 2: Open Swagger UI in browser
```
http://localhost:8000/docs
```

### Step 3: Prepare your file

**Option A: Use the converter script I made**
```bash
python convert_to_base64.py resume.pdf
```

This will print JSON that looks like:
```json
{
  "fileName": "resume.pdf",
  "fileContent": "JVBERi0xLjQKJe..."
}
```

**Option B: Use online converter**
1. Go to: https://base64.guru/converter/encode/file
2. Upload your PDF/DOCX file
3. Click "Encode file to Base64"
4. Copy the base64 string

### Step 4: Test in Swagger UI

1. Click on **"POST /parse/resume"** (or /parse/jd)
2. Click **"Try it out"** button
3. You'll see a JSON template in the Request body:
   ```json
   {
     "fileName": "string",
     "fileContent": "string"
   }
   ```
4. Replace it with your actual data:
   ```json
   {
     "fileName": "resume.pdf",
     "fileContent": "JVBERi0xLjQKJeLjz9MKMSAwIG9iago8PC9UeXBlL0NhdGFsb2cvUGFnZXMgMiAwIFI+PmVuZG9iagoyIDAgb2JqPDwvVHlwZS9QYWdlcy9LaWRzWzMgMCBSXS9Db3VudCAxPj5lbmRvYmog..."
   }
   ```
5. Click **"Execute"** button
6. Scroll down to see the response!

---

## Method 2: Using Python Script (I Made This For You!)

### Step 1: Start your server (in one terminal)
```bash
python main.py
```

### Step 2: Run test script (in another terminal)

**For Resume:**
```bash
python test_api.py path/to/resume.pdf
```

**For Job Description:**
```bash
python test_api.py path/to/jd.pdf jd
```

### Example:
```bash
# If your resume is on desktop
python test_api.py C:\Users\YourName\Desktop\resume.pdf

# Mac/Linux
python test_api.py ~/Desktop/resume.pdf
```

**The script will:**
-  Read your file
-  Convert to base64 automatically
-  Send to API
-  Show you the JSON response

---

## Method 3: Using Postman (For API Testing)

### Step 1: Download Postman
- Go to: https://www.postman.com/downloads/
- Install it (it's free)

### Step 2: Start your server
```bash
python main.py
```

### Step 3: In Postman

1. **Create New Request**
   - Click "New" → "HTTP Request"

2. **Set Request Type**
   - Change from GET to **POST**

3. **Enter URL**
   ```
   http://localhost:8000/parse/resume
   ```

4. **Set Headers**
   - Click "Headers" tab
   - Add: `Content-Type: application/json`

5. **Set Body**
   - Click "Body" tab
   - Select "raw"
   - Select "JSON" from dropdown
   - Paste your JSON:
   ```json
   {
     "fileName": "resume.pdf",
     "fileContent": "your_base64_string_here"
   }
   ```

6. **Click Send**
   - You'll see the response below!

---

## Method 4: Using cURL (Command Line)

### For Resume:
```bash
curl -X POST "http://localhost:8000/parse/resume" \
  -H "Content-Type: application/json" \
  -d '{
    "fileName": "resume.pdf",
    "fileContent": "JVBERi0xLjQKJe..."
  }'
```

### For Job Description:
```bash
curl -X POST "http://localhost:8000/parse/jd" \
  -H "Content-Type: application/json" \
  -d '{
    "fileName": "job.pdf",
    "fileContent": "JVBERi0xLjQKJe..."
  }'
```

---

## Method 5: Write Your Own Python Script

Create a file called `my_test.py`:

```python
import requests
import base64

# 1. Read your file
with open("resume.pdf", "rb") as f:
    file_content = base64.b64encode(f.read()).decode()

# 2. Prepare JSON
data = {
    "fileName": "resume.pdf",
    "fileContent": file_content
}

# 3. Send POST request
response = requests.post(
    "http://localhost:8000/parse/resume",
    json=data
)

# 4. Print result
print(response.json())
```

Run it:
```bash
python my_test.py
```

---

##  Understanding the Response

### For Resume, you'll get:
```json
{
  "personal_detail": {
    "full_name": "John Doe",
    "email": "john@example.com",
    "contact_no": "+1234567890",
    "gender": "Male",
    "nationality": "American"
  },
  "address": {
    "address": "123 Main St",
    "city": "New York",
    "state": "NY",
    "country": "USA",
    "zip_code": "10001"
  },
  "education": [
    {
      "degree": "Bachelor of Science in Computer Science",
      "school": "MIT",
      "start_date": "2018",
      "end_date": "2022"
    }
  ],
  "experience": [
    {
      "job_title": "Software Engineer",
      "company_name": "Google",
      "start_date": "2022",
      "end_date": "Present",
      "projects": "Worked on search algorithms"
    }
  ],
  "skills": ["Python", "JavaScript", "React", "AWS"],
  "certifications": ["AWS Certified Developer"]
}
```

### For Job Description, you'll get:
```json
{
  "job_detail": {
    "job_position": "Senior Software Engineer",
    "job_type": "Full-time",
    "job_shift": "Day",
    "job_industry": "Technology",
    "closing_date": "2024-12-31",
    "min_experience": 3,
    "max_experience": 7,
    "no_of_openings": 2,
    "required_education": ["Bachelor's in Computer Science"],
    "job_description": "We are looking for..."
  },
  "salary_range": {
    "min_amount": 100000,
    "max_amount": 150000
  },
  "job_location": {
    "city": "San Francisco",
    "state": "CA",
    "country": "USA",
    "zip_code": "94102"
  },
  "required_skills": ["Python", "FastAPI", "Docker", "AWS"]
}
```

---

##  Step-by-Step Example (Complete Walkthrough)

Let's do it together!

### Step 1: Create a sample resume
Create a file called `sample_resume.txt`:
```
John Doe
Email: john.doe@email.com
Phone: +1-234-567-8900
Address: 123 Main Street, New York, NY 10001

EDUCATION
Bachelor of Science in Computer Science
Massachusetts Institute of Technology
2018 - 2022

EXPERIENCE
Software Engineer
Google Inc.
2022 - Present
Developed search algorithms and improved performance by 30%

SKILLS
Python, JavaScript, React, AWS, Docker, Kubernetes

CERTIFICATIONS
AWS Certified Solutions Architect
```

Save it as DOCX (using Word or Google Docs)

### Step 2: Convert to base64
```bash
python convert_to_base64.py sample_resume.docx
```

### Step 3: Copy the output
You'll see something like:
```json
{
  "fileName": "sample_resume.docx",
  "fileContent": "UEsDBBQABgAIAAAA..."
}
```

### Step 4: Open browser
```
http://localhost:8000/docs
```

### Step 5: Test
1. Click on POST /parse/resume
2. Click "Try it out"
3. Paste the JSON
4. Click "Execute"
5. See the magic! ✨

---

## 🐛 Common Issues

### Issue 1: "Could not connect to API"
**Solution:** Make sure server is running
```bash
python main.py
```
Look for: "Uvicorn running on http://0.0.0.0:8000"

### Issue 2: "Invalid base64 string"
**Solution:** Use the converter script
```bash
python convert_to_base64.py your_file.pdf
```

### Issue 3: "No text could be extracted"
**Solution:** 
- Make sure file is valid PDF/DOCX
- File is not corrupted
- File contains actual text (not just images)

### Issue 4: Server returns 500 error
**Solution:**
- Check if GROQ_API_KEY is set
- Check server terminal for error details
- Verify internet connection (Groq needs internet)

---

##  Pro Tips

### Tip 1: Keep server running
- Don't close the terminal where server is running
- Open a new terminal for testing

### Tip 2: Check server logs
- Server terminal shows all requests
- Helpful for debugging
- You can see what's happening in real-time

### Tip 3: Start simple
- Test with a simple resume first
- Then try complex ones
- Then try job descriptions

### Tip 4: Save examples
- Keep sample files for demo
- Save the JSON outputs
- Great for showing your team

### Tip 5: Use the test script
- Fastest way to test
- No need to convert to base64 manually
- Just: `python test_api.py resume.pdf`

---

##  Recommended Testing Flow

**For First Time:**
1. Use Swagger UI (http://localhost:8000/docs)
2. Use the converter script to get base64
3. Test with simple resume
4. Look at the response
5. Understand the structure

**For Regular Testing:**
1. Use the test_api.py script
2. Just: `python test_api.py your_file.pdf`
3. Quick and easy!

**For Integration:**
1. Use Postman to build your request
2. Generate code from Postman
3. Copy to your application

---

## 🚀 Next Steps

After testing:
1.  Verify output is correct
2.  Try different resume formats
3.  Test with job descriptions
4.  Show to your team
5.  Integrate with frontend

---

##  Quick Reference

**Start Server:**
```bash
python main.py
```

**Test with Script:**
```bash
python test_api.py resume.pdf
```

**Convert File:**
```bash
python convert_to_base64.py resume.pdf
```

**Open API Docs:**
```
http://localhost:8000/docs
```

**Endpoints:**
- Resume: `POST http://localhost:8000/parse/resume`
- Job Desc: `POST http://localhost:8000/parse/jd`

---

That's it! You're ready to test! 
