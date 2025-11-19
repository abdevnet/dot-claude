A collection of skills and agents for claude.  Currently the main skills I am using are the code-review-skill along with the batch-code-analysis-skill.
To use clone this repo into your local .claude folder.  Or download the skills and agents folder and copy those folders to your .claude folder.

To try it out after updating your local .claude folder start claude code in the terminal inside of your code repo.  Ask claude to do a code review.

There are known issues where claude doesn't always invoke the skill that it should.  I put this line in my main 
Claude.MD file to make sure the skills activate.  Some developers use hooks to accomplish this.

   ```   
     Always use the batch-code-analysis-skill to break the work up into tasks running in parallel when asked to do a code review. 
     Each task should use the code-review-skill.
   ```