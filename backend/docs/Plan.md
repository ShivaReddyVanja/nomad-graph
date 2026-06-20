We are building a travel platform where we use multi agent architecture to create the entire iternary. 
we will be using langgraph for core agent orchestration, we will have multiple nodes of agents. 
We will have a entry node named Gatekeeper, who takes in the prompt and asks the questions about gaps in the given prompt, lets say a user gives a prompt of iternary, but they dont mention their budget, types of activities they like, or number of days they want to travel. etc. 

Once the gaps are filled, our gatekeeper passes this info down to the core orchestrator, who is called captain , whose responsibility is to breakdown tasks and allot the tasks to individual agents and validate their responses.

We will have worker agents like travel agent, stay agent, sightseeing or activity agent, food agent, and some other agents maybe.

We need external tools/ APIs for fetching data like flights, trains, buses and estimate travel times and prices for travel. 

We also need tools for fetching stay places like hotels, homestays or dormitories.

Then we need food tools and sightseeing places tools. 

We need tools like mathematical tools like multiplication, subtraction,division and complex math operations. 

This is for now. 

