1. Fork the repository
2. Create a new branch (`git checkout -b feature-branch`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add some feature'`)
5. Push to the branch (`git push origin feature-branch`)
6. Open a pull request

## Formatting and Linting
To format & lint the code before committing, you must run the following two commands:

`black atomic_agents`

`flake8 atomic_agents`


## Testing
To run the tests, run the following command:
`pytest --cov atomic_agents`

To view the coverage report, run the following command:
`coverage html`
