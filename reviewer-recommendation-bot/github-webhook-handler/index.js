var request = require('request')

const recommendationEngineUrl = 'http://recommendation-engine:8080'
const dbUpdateUrl = 'http://db-updater:8081'

module.exports = (app) => {
	// Your code here
	app.log('Yay! The app was loaded!')

	// example of probot responding 'Hello World' to a new issue being opened
	app.on('issues.opened', async context => {
		console.log(context)
		const params = context.issue({body: 'Hello World!'})
		return context.github.issues.createComment(params)
	})

	app.on('pull_request.opened', async context => {
		const payload = context.payload
		const prNumber = payload.number
		const repo = payload.repository.name
		const owner = payload.repository.owner.login
		const title = payload.pull_request.title
		const pull = (await context.github.issues.get(context.issue())).data
		const diffUrl = pull.pull_request.diff_url

		const params = context.issue()
		const modifiedFiles = (await context.github.pullRequests.getFiles(params)).data

		// Send details to the recommendation engine
		request.post({
				url: recommendationEngineUrl,
				body: modifiedFiles,
				json: true
			},
			function (err, httpResponse, responseBody) {
				if (err) {
					console.log('ERROR: ' + err)
				}
				const responseString = 'Recommended reviewers: @' + responseBody
				const commentParams = context.issue({body: responseString})
				context.github.issues.createComment(commentParams)
				console.log('RESPONSE BODY: ' + responseBody)
			}
		)
	})

	app.on('pull_request.closed', async context => {
		const commentParams = context.issue({body: 'Thanks for using the bot. Would you like to take a survey?\nhttps://goo.gl/forms/PvrHlLwBcRFbp2cp1 '})
		context.github.issues.createComment(commentParams)
	})

	app.on('push', async context => {
		app.log('New push (commits) Commit ID: ' + context.payload.after)
		const payload = context.payload
		const owner = payload.repository.owner.login
		const repo = payload.repository.name

		let requestBody = {
			owner: owner,
			repo: repo,
			commits: payload.commits
		}

		request.post({
				url: dbUpdateUrl + '/push',
				body: requestBody,
				json: true
			},
			function (err, httpResponse, responseBody) {
				if (err) {
					console.log('ERROR: ' + err)
				}
				console.log('RESPONSE BODY: ' + responseBody)
			}
		)
	})
}
