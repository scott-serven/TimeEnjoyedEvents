const feed = new EventSource('https://codejam.timeenjoyed.dev/api/github/commit_feed');
const notifSound = new Audio('notif.mp3');

let count = 0;
const queue = Array();


function handleTimeout() {
    const cardWrapper = document.querySelector('#wrapper');
    const githubCard = queue[0];

    setTimeout(() => {
        githubCard.classList.remove('active');
        queue.shift();

        if (queue.length) {
            handleTimeout();
        }
    }, 7000);

    setTimeout(() => {
        cardWrapper.removeChild(githubCard);
    }, 7300);

}


feed.onmessage = (ev) => {
    count ++;

    const cardWrapper = document.querySelector('#wrapper');
    const data = JSON.parse(ev.data);

    const githubCardHTML =
        `
            <div class="githubCardWrapper" id="card${count}">
                <div class="githubCard">

                    <div class="header">
                        <img class="authorAvatar" src="${data['sender']['avatar']}">
                        <span>${data['sender']['name']} - (${data['team']['name']})</span>
                    </div>
            
                    <div class="commits">
                        ${data['commits'].map((commit) => {
                    return(`<span><b>${commit['author']} - </b>${commit['message']}</span>`)
                            }).join('')}
                        
                        <span><b>${data['commit_length']} new commits...</b></span>
                    </div>
                </div>
                
                <img src="github.gif" class="githubCardImage">
            </div>`

    cardWrapper.insertAdjacentHTML('beforeend', githubCardHTML);
    const githubCard = document.querySelector(`#card${count}`);
    githubCard.classList.add('active');

    if (!queue.length) {
        notifSound.play()
        queue.push(githubCard);
        handleTimeout();
    }

    else {
        queue.push(githubCard);
    }

};