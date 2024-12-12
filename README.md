# discord-tag-post-bot
 Add tags to discord posts with attachments

## Summary
This is a Discord bot that allows users to tag posts containing attachments, and fetch posts later based on specified tags. A post can have any number of tags. This bot is being built to run on a local machine, and has not been tested hosted on cloud.

## Commands
### Slash Commands
`/tag`: Add a list of tags to the previous post in the channel. 
`/tags`: Retrieve a list of all tags in this server
`/fetch`: Retrieve a random post that matches a single provided tag
`/fetch_any`: Retrieve a random post that matches at least one of any number of provided tags
`/fetch_match`: Retrieve a random post that matches all of any number of provided tags.
`/untag`: Remove any number of provided tags from the previous post in the channel
`/untagall`: Remove all tags from the previous post in the channel
`/sync`: Debugging command that syncs the Tags and Posts lists with eachother, and refreshes the files.

### Exclaimation Commands
`!tag`: Add a list of tags to the current message, or a message being replied to
`!untag`: Removes a list of tags from a message being replied to
`!untagall`: Removes all tags from a message being replied to