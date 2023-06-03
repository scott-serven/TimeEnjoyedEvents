const feed = new EventSource('https://codejam.timeenjoyed.dev/api/teams/feed_event');


const langs = {
    0: 'No Preference',
    1: 'Python',
    2: 'JavaScript',
    3: 'TypeScript',
    4: 'Java',
    5: 'Kotlin',
    6: 'C++',
    7: 'C',
    8: 'C#',
    9: 'Rust',
    10: 'Go',
    11: 'Swift',
    12: 'Bash/Shell',
    13: 'Lua',
    14: 'VisualBasic',
    15: 'Haskell',
    16: 'Dart',
    17: 'PHP',
    18: 'Other...'
}


feed.onmessage = async (ev) => {
    const data = JSON.parse(ev.data);
    const container = document.querySelector('.container');
    container.innerHTML = '<h2>CodeJam Team Feed</h2>';

    for (let team in data) {
        const members = data[team];

        if (team === "null") {
            team = 'No Current Team';
        }

        const team_id = `A-${team.replace(/\s+/g, '-').toLowerCase()}-B`;

        const teamContainerHTML = `
            <div class="teamContainer" id=${team_id}>
                <h2 class="teamHeader">${team}</h2>
            </div>
        `

        container.insertAdjacentHTML('beforeend', teamContainerHTML);

        const teamContainer = document.querySelector(`#${team_id}`);
        for (let member of members) {
            const memberHTML = `
                <div class="teamMemberContainer">
                    <div class="teamMemberPopover">
                        <b>Solo?</b>
                        <hr>
                        <span>${member['solo'] === true ? 'True' : 'False'}</span>
                        <br>
                        <b>Languages</b>
                        <hr>
                        ${member['languages'].map((lang) => {
                            return(`<span>${langs[lang]}</span>`)
                        }).join('')}
                        <br>
                        <b>Timezone</b>
                        <hr>
                        <span>UTC${member['timezone'] > 0 ? '+' : ''}${member['timezone']}</span>
                    </div>
                    <img class="teamMemberImage" src="${member['avatar']}">
                    <span>${member['name']}</span>
                </div>
            `

            teamContainer.insertAdjacentHTML('beforeend', memberHTML);
        }
    }
}