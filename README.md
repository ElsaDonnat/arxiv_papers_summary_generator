Hi! I am a self-taught AI enthousiast, who likes to learn by trying out things!

This python script uses the Arxiv.org API to fetch the most recent papers (you can change the number and dates through the parameters in the script) in the ML/AI category.
Their content is isolated and stored in a .json file.
The script then accesses the open-source LLM Bert through the HuggingFace API (you need to imput your HuggingFace token, which is free but limited in terms of workload).
Bert is then prompted to summarize each paper provided, and the script stores them in a new .json file.

For the next steps of my project, I am going to try to improve the summary quality by fine-tuning Bert through the HuggingFace platform, 
and using the fine-tuned version in my script insead. 

The final project is to have the script run automatically once a week, and automatically prepare and send a newsletter out of the summaries.  
