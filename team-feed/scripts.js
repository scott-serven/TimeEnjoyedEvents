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

function showPopup(e, member) {
    const header = document.querySelector('#memberInfoPopupHeader');
    const popup = document.querySelector('#memberInfoPopup');
    const languages = document.querySelector('#memberLanguages');
    const timezone = document.querySelector('#memberTimeZone');
    header.innerHTML = `${member['name']}`;
    languages.innerHTML = `
        <ul>
        ${member['languages'].map((lang) => {
        return(`<li>${langs[lang]}</li>`)
    }).join('')}
        </ul>
    `
    timezone.innerHTML = `
        <span>GMT${member['timezone'] > 0 ? '+' : ''}${member['timezone']}</span>
    `
    const rect = e.target.getBoundingClientRect();
    const docRect = document.documentElement.getBoundingClientRect();

    // always reset since we might switch sides since last display
    popup.style.left = '';
    popup.style.right = '';
    popup.style.top = '';
    popup.style.bottom = '';

    // position popup so it fits on the screen
    if (rect.top > docRect.height / 2) {
        popup.style.bottom = (docRect.height - rect.y - rect.height) + 'px';
    } else {
        popup.style.top = rect.y + 'px';
    }

    if (rect.left > docRect.width / 2) {
        popup.style.right = (docRect.width - rect.x) + 25 + 'px';
    } else {
        popup.style.left = rect.x + rect.width + 25 + 'px';
    }

    popup.style.visibility = 'visible';
}

function closePopup(e) {
    const popup = document.querySelector('#memberInfoPopup');
    e.target.style.zIndex = '0';
    popup.style.left = '';
    popup.style.right = '';
    popup.style.top = '';
    popup.style.bottom = '';
    popup.style.visibility = 'hidden';
}

function formatMember(member) {
    return `
        <img class="teamMemberImage" src="${member['avatar']}"/>
        <div class="teamMemberName">${member['name']}</div>
    `;
}

function addMemberPopupEvents(memberContainer, member) {
    const memberHoverElement = memberContainer.querySelector('.teamMemberImage');
    memberHoverElement.addEventListener('click', (event) => {
        showPopup(event, member);
    });
    memberHoverElement.addEventListener('mouseenter', (event) => {
        showPopup(event, member);
    });
    memberHoverElement.addEventListener('mouseleave', (event) => {
        closePopup(event);
    });
}

function createMemberContainer(parent, member) {
    let memberContainer = document.createElement('div');
    memberContainer.className = 'teamMemberContainer';
    memberContainer.innerHTML = formatMember(member);
    parent.appendChild(memberContainer);
    addMemberPopupEvents(memberContainer, member);
    return memberContainer;
}

function updateLookingForGroupData(data) {
    const MAX_TZ = 25; // not sure the range we allowed for signups, but we need an extra timezone for some reason
    const container = document.querySelector('.unassignedMembers');
    container.innerHTML = '';

    let tzColumns = [];
    for (let x = 0; x < MAX_TZ; x++) {
        let col = document.createElement('div');
        col.className = 'lfgMemberColumn';
        container.appendChild(col);
        tzColumns.push(col);
    }

    for (let team in data) {
        const members = data[team];
        if (team === "None") {
            for (let member of members) {
                if (member['solo'] === false) {
                    let tzColIndex = member['timezone'] + 12;
                    createMemberContainer(tzColumns[tzColIndex], member);
                    tzColumns[tzColIndex].style.paddingTop = (tzColIndex % 2 === 0 ? '1em' : '7em');
                }
            }
        }
    }
}

function updateTeamData(data) {
    const container = document.querySelector('.teamsInnerContainer');
    container.innerHTML = '';

    for (let team in data) {
        const members = data[team];

        if ((team !== "None") && (team !== "CodeJam Managers")) {
            // teams that consist of only one member that's a "solo" member, doesn't count as a team
            let allSoloTeam = members.reduce((acc, curr) => acc && curr['solo'], true);
            if (!allSoloTeam) {
                const teamDiv = document.createElement('div');
                teamDiv.className = 'teamContainer';
                teamDiv.insertAdjacentHTML('beforeend', `<header>${team}</header>`);
                for (let member of members) {
                    createMemberContainer(teamDiv, member);
                }
                container.appendChild(teamDiv);
            }
        }
    }
}

function updateSoloData(data) {
    const container = document.querySelector('.soloInnerContainer');
    container.innerHTML = '';

    for (let team in data) {
        const members = data[team];

        if (team !== "CodeJam Managers") {
            let allSoloTeam = true;
            if (team !== "None") {
                allSoloTeam = members.reduce((acc, curr) => acc && curr['solo'], true);
            }
            if (allSoloTeam) {
                for (let member of members) {
                    if (member['solo'] === true) {
                        createMemberContainer(container, member);
                    }
                }
            }
        }
    }
}

function updateCodeJamManagers(data) {
    const container = document.querySelector('.codeJamManagers');
    container.innerHTML = '<h3>CodeJam Managers</h3>';

    for (let team in data) {
        const members = data[team];

        if (team === "CodeJam Managers") {
            for (let member of members) {
                createMemberContainer(container, member);
            }
        }
    }
}

feed.onmessage = async (ev) => {
    const data = JSON.parse(ev.data);

    updateTeamData(data);
    updateLookingForGroupData(data);
    updateSoloData(data);
    updateCodeJamManagers(data);
}